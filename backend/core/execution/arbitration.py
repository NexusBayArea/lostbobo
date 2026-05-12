from __future__ import annotations

from typing import TYPE_CHECKING

from backend.core.execution.models import ExecutionRequest
from backend.core.scheduler.scheduler_models import ResourceRequest, Workload, WorkloadPriority, WorkloadType

if TYPE_CHECKING:
    from backend.core.scheduler.kernel_scheduler import KernelScheduler


class ResourceArbiter:
    def __init__(
        self,
        scheduler: KernelScheduler,
        api_cost_per_second: float = 0.0002,
    ):
        self.scheduler = scheduler
        self.api_cost_per_second = api_cost_per_second

    async def can_dispatch(self, request: ExecutionRequest) -> bool:
        workload = Workload(
            tenant_id=request.tenant_id,
            plugin_name=request.plugin_name,
            workload_type=WorkloadType.SIMULATION,
            priority=WorkloadPriority.NORMAL,
            resources=ResourceRequest(
                gpu_fraction=1.0,
                gpu_type="a40",
                max_runtime_seconds=request.timeout_seconds,
            ),
        )

        candidates = self.scheduler.resources.available_nodes(workload.resources)
        if not candidates:
            return False

        return True
