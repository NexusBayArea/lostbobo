from __future__ import annotations

import asyncio
import os
from typing import Dict, Optional

from backend.core.execution.arbitration import ResourceArbiter
from backend.core.execution.models import ExecutionFuture, ExecutionRequest, ExecutionStatus
from backend.core.execution.queue import KernelExecutionQueue
from backend.core.execution.runpod_client import RunPodClient
from backend.core.execution.streaming import SimulationEvent, SimulationStreamManager


class SimulationExecutor:
    def __init__(
        self,
        queue: KernelExecutionQueue,
        arbiter: ResourceArbiter,
        runpod: RunPodClient,
        stream_mgr: SimulationStreamManager,
    ):
        self.queue = queue
        self.arbiter = arbiter
        self.runpod = runpod
        self.stream_mgr = stream_mgr
        self._active_jobs: Dict[str, asyncio.Task] = {}
        self._cpu_endpoint_id = os.getenv("RUNPOD_CPU_ENDPOINT")
        self._gpu_endpoint_id = os.getenv("RUNPOD_A40_ENDPOINT")

    async def submit(self, request: ExecutionRequest) -> ExecutionFuture:
        future = ExecutionFuture(execution_id=request.execution_id)
        await self.queue.enqueue(request)
        return future

    async def cancel(self, execution_id: str) -> bool:
        task = self._active_jobs.pop(execution_id, None)
        if task is not None:
            task.cancel()
            self.queue.mark_completed(execution_id)
            await self.stream_mgr.push_event(
                execution_id,
                SimulationEvent(
                    execution_id=execution_id,
                    event_type="cancelled",
                    data={},
                ),
            )
            return True
        return False

    async def get_status(self, execution_id: str) -> Optional[ExecutionStatus]:
        if execution_id in self._active_jobs:
            return ExecutionStatus.RUNNING
        if self.queue.leases.is_leased(execution_id):
            return ExecutionStatus.LEASED
        return ExecutionStatus.QUEUED

    async def run_dispatcher(self):
        while True:
            request = await self.queue.dequeue()
            if request is None:
                await asyncio.sleep(1)
                continue

            if not await self.arbiter.can_dispatch(request):
                await self.queue.enqueue(request)
                await asyncio.sleep(5)
                continue

            await self.stream_mgr.start_stream(request.execution_id)

            task = asyncio.create_task(self._execute(request))
            self._active_jobs[request.execution_id] = task
            task.add_done_callback(lambda t: self._active_jobs.pop(request.execution_id, None))

    async def _execute(self, request: ExecutionRequest):
        try:
            job_id = await self.runpod.submit_job(
                self._gpu_endpoint_id,
                payload={
                    "execution_id": request.execution_id,
                    "capability": request.capability,
                    "inputs": request.inputs,
                    "tenant_id": request.tenant_id,
                },
            )
            await self._poll_and_stream(request.execution_id, job_id)
            self.queue.mark_completed(request.execution_id)
            await self.stream_mgr.push_event(
                request.execution_id,
                SimulationEvent(
                    execution_id=request.execution_id,
                    event_type="completed",
                    data={},
                ),
            )
        except Exception as e:
            if self.queue.mark_failed(request.execution_id):
                await self.queue.requeue(request)
            await self.stream_mgr.push_event(
                request.execution_id,
                SimulationEvent(
                    execution_id=request.execution_id,
                    event_type="failed",
                    data={"error": str(e)},
                ),
            )

    async def _poll_and_stream(self, execution_id: str, job_id: str):
        while True:
            status = await self.runpod.get_job_status(job_id)
            state = status.get("status")

            if state == "COMPLETED":
                await self.stream_mgr.push_event(
                    execution_id,
                    SimulationEvent(
                        execution_id=execution_id,
                        event_type="result",
                        data=status.get("output", {}),
                    ),
                )
                break
            elif state == "FAILED":
                raise RuntimeError(status.get("error", "Job failed on RunPod"))
            elif state == "IN_PROGRESS":
                for item in status.get("stream", []):
                    await self.stream_mgr.push_event(
                        execution_id,
                        SimulationEvent(
                            execution_id=execution_id,
                            event_type="partial",
                            data=item,
                        ),
                    )
                await self.stream_mgr.push_event(
                    execution_id,
                    SimulationEvent(
                        execution_id=execution_id,
                        event_type="telemetry",
                        data={
                            "runtime_remaining": status.get("delayTime", 30),
                        },
                    ),
                )
            await asyncio.sleep(2)
