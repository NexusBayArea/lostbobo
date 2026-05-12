from __future__ import annotations

import traceback

from backend.core.protocol.bus.protocol_envelope import ProtocolEnvelope
from backend.core.protocol.bus.protocol_response import ProtocolResponse
from backend.core.protocol.contracts.base_protocol import BaseProtocol
from backend.core.scheduler.scheduler_models import ResourceRequest, Workload, WorkloadPriority, WorkloadType


class SchedulerProtocol(BaseProtocol):
    protocol_name = "scheduler"

    async def handle(self, envelope: ProtocolEnvelope) -> ProtocolResponse:
        action = envelope.action
        payload = envelope.payload

        if action == "schedule":
            return await self._handle_schedule(envelope, payload)
        elif action == "release":
            return await self._handle_release(envelope, payload)
        elif action == "query_resources":
            return await self._handle_query_resources(envelope, payload)
        else:
            return ProtocolResponse(
                success=False,
                error=f"Unknown scheduler action: {action}",
            )

    async def _handle_schedule(self, envelope: ProtocolEnvelope, payload: dict) -> ProtocolResponse:
        try:
            scheduler = getattr(self, "_kernel_services", {}).get("scheduler")
            if scheduler is None:
                return ProtocolResponse(
                    success=False,
                    error="KernelScheduler not available",
                )

            workload = Workload(
                tenant_id=envelope.tenant_id,
                plugin_name=envelope.source,
                workload_type=WorkloadType(payload.get("workload_type", "simulation")),
                priority=WorkloadPriority(payload.get("priority", "normal")),
                resources=ResourceRequest(
                    cpu_cores=payload.get("cpu_cores", 1.0),
                    memory_mb=payload.get("memory_mb", 1024),
                    gpu_fraction=payload.get("gpu_fraction", 0.0),
                    gpu_type=payload.get("gpu_type"),
                    max_runtime_seconds=payload.get("max_runtime", 300),
                ),
                dag_id=payload.get("dag_id"),
            )

            result = await scheduler.schedule(workload)
            return ProtocolResponse(
                success=result.get("status") == "accepted",
                payload=result,
            )
        except Exception as e:
            return ProtocolResponse(
                success=False,
                error=f"Scheduler dispatch failed: {e}",
                payload={"traceback": traceback.format_exc()},
            )

    async def _handle_release(self, envelope: ProtocolEnvelope, payload: dict) -> ProtocolResponse:
        try:
            scheduler = getattr(self, "_kernel_services", {}).get("scheduler")
            if scheduler is None:
                return ProtocolResponse(
                    success=False,
                    error="KernelScheduler not available",
                )

            workload_id = payload.get("workload_id")
            if not workload_id:
                return ProtocolResponse(
                    success=False,
                    error="workload_id required",
                )

            workload = scheduler.active_workloads.pop(workload_id, None)
            if workload is None:
                return ProtocolResponse(
                    success=False,
                    error=f"Unknown workload: {workload_id}",
                )

            await scheduler.release_resources(workload)
            return ProtocolResponse(
                success=True,
                payload={"workload_id": workload_id},
            )
        except Exception as e:
            return ProtocolResponse(
                success=False,
                error=f"Scheduler release failed: {e}",
            )

    async def _handle_query_resources(self, envelope: ProtocolEnvelope, payload: dict) -> ProtocolResponse:
        try:
            scheduler = getattr(self, "_kernel_services", {}).get("scheduler")
            if scheduler is None:
                return ProtocolResponse(
                    success=False,
                    error="KernelScheduler not available",
                )

            req = ResourceRequest(
                gpu_fraction=payload.get("gpu_fraction", 0.0),
                gpu_type=payload.get("gpu_type"),
            )
            candidates = scheduler.resources.available_nodes(req)
            return ProtocolResponse(
                success=True,
                payload={
                    "available_nodes": [
                        {"node_id": node_id, "available": node.available} for node_id, node in candidates
                    ]
                },
            )
        except Exception as e:
            return ProtocolResponse(
                success=False,
                error=f"Resource query failed: {e}",
            )
