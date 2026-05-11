from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.core.scheduler.scheduler_models import Workload


class BudgetEngine:
    # cost per GPU fraction per second (example)
    COST_PER_GPU_SECOND = 0.0001

    async def can_afford(self, workload: "Workload") -> bool:
        if workload.budget_limit_usd is None:
            return True
        est_cost = workload.resources.gpu_fraction * self.COST_PER_GPU_SECOND * workload.resources.max_runtime_seconds
        return est_cost <= workload.budget_limit_usd
