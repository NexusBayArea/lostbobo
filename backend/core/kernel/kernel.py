from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from backend.core.execution.queue import KernelExecutionQueue
from backend.core.execution.runpod_client import RunPodClient
from backend.core.execution.streaming import SimulationStreamManager
from backend.core.sdk.capability_registry import CapabilityRegistry
from backend.core.sdk.dag_node_registry import DAGNodeRegistry
from backend.core.sdk.plugin_loader import PluginLoader

if TYPE_CHECKING:
    from backend.core.execution.arbitration import ResourceArbiter
    from backend.core.execution.simulation_executor import SimulationExecutor
    from backend.core.hardware.isolation import GPUIsolationManager
    from backend.core.scheduler.kernel_scheduler import KernelScheduler


class SimHPCKernel:
    def __init__(self) -> None:
        self.logger = logging.getLogger("simhpc.kernel")

        self.capabilities = CapabilityRegistry()
        self.dag = DAGNodeRegistry()
        self.plugin_loader = PluginLoader(kernel=self)

        self.scheduler: KernelScheduler | None = None
        self.execution_queue: KernelExecutionQueue | None = None
        self.simulation_executor: SimulationExecutor | None = None
        self.stream_manager: SimulationStreamManager | None = None
        self._dispatcher_task: asyncio.Task | None = None

    async def boot(self) -> None:
        self.logger.info("Booting SimHPC Kernel...")

        from backend.core.execution.arbitration import ResourceArbiter
        from backend.core.execution.simulation_executor import SimulationExecutor
        from backend.core.hardware.isolation import GPUIsolationManager
        from backend.core.scheduler.kernel_scheduler import KernelScheduler

        self.scheduler = KernelScheduler(gpu_manager=GPUIsolationManager.manager())
        self.logger.info("KernelScheduler initialized")

        self.execution_queue = KernelExecutionQueue()
        self.logger.info("KernelExecutionQueue initialized")

        runpod = RunPodClient()
        self.stream_manager = SimulationStreamManager()
        arbiter = ResourceArbiter(scheduler=self.scheduler)

        self.simulation_executor = SimulationExecutor(
            queue=self.execution_queue,
            arbiter=arbiter,
            runpod=runpod,
            stream_mgr=self.stream_manager,
        )
        self.logger.info("SimulationExecutor initialized")

        await self._register_capabilities()

        await self.plugin_loader.load_plugins()

        self._dispatcher_task = asyncio.create_task(self.simulation_executor.run_dispatcher())
        self.logger.info("Execution dispatcher started")

        self.logger.info("Kernel boot complete.")

    async def _register_capabilities(self):
        self.capabilities.register("execution.submit", self.simulation_executor.submit)
        self.capabilities.register("execution.cancel", self.simulation_executor.cancel)
        self.capabilities.register("execution.status", self.simulation_executor.get_status)

    async def shutdown(self) -> None:
        self.logger.info("Shutting down SimHPC Kernel...")

        if self._dispatcher_task is not None:
            self._dispatcher_task.cancel()
            try:
                await self._dispatcher_task
            except asyncio.CancelledError:
                pass
            self.logger.info("Execution dispatcher stopped")

        self.logger.info("Kernel shutdown complete.")
