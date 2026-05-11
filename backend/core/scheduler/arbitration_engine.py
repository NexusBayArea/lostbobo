class ArbitrationEngine:
    def __init__(self, fairness, budgets, thermal):
        self.fairness = fairness
        self.budgets = budgets
        self.thermal = thermal

    async def evaluate(self, workload) -> bool:
        if not self.fairness.can_schedule(workload.tenant_id, workload.resources.gpu_fraction):
            return False
        if not await self.budgets.can_afford(workload):
            return False
        return True
