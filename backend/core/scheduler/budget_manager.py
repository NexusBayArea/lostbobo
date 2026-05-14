from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class Budget:
    tenant_id: str
    total_credits: float
    consumed_credits: float = 0.0
    reserved_credits: float = 0.0
    reset_period_hours: int = 24
    last_reset: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CostModel:
    cpu_cost_per_core_second: float = 0.0001
    memory_cost_per_gb_second: float = 0.00005
    gpu_cost_per_second: float = 0.01
    gpu_dedicated_cost_per_second: float = 0.05


class BudgetManager:
    def __init__(self, cost_model: CostModel | None = None):
        self.budgets: dict[str, Budget] = {}
        self.cost_model = cost_model or CostModel()
        self._lock = asyncio.Lock()

    async def set_budget(self, tenant_id: str, credits: float) -> None:
        async with self._lock:
            self.budgets[tenant_id] = Budget(tenant_id=tenant_id, total_credits=credits)

    async def can_afford(self, tenant_id: str, estimated_cost: float) -> bool:
        async with self._lock:
            budget = self.budgets.get(tenant_id)
            if budget is None:
                return True
            available = budget.total_credits - budget.consumed_credits - budget.reserved_credits
            return available >= estimated_cost

    async def reserve(self, tenant_id: str, estimated_cost: float) -> bool:
        async with self._lock:
            budget = self.budgets.get(tenant_id)
            if budget is None:
                return True
            available = budget.total_credits - budget.consumed_credits - budget.reserved_credits
            if available < estimated_cost:
                return False
            budget.reserved_credits += estimated_cost
            return True

    async def commit(self, tenant_id: str, actual_cost: float) -> None:
        async with self._lock:
            budget = self.budgets.get(tenant_id)
            if budget:
                budget.reserved_credits = max(0, budget.reserved_credits - actual_cost)
                budget.consumed_credits += actual_cost

    async def release_reservation(self, tenant_id: str, reserved_cost: float) -> None:
        async with self._lock:
            budget = self.budgets.get(tenant_id)
            if budget:
                budget.reserved_credits = max(0, budget.reserved_credits - reserved_cost)

    def estimate_cost(
        self,
        cpu_cores: float,
        memory_mb: int,
        gpu_seconds: float,
    ) -> float:
        cpu_cost = cpu_cores * self.cost_model.cpu_cost_per_core_second
        memory_cost = (memory_mb / 1024) * self.cost_model.memory_cost_per_gb_second
        gpu_cost = gpu_seconds * self.cost_model.gpu_cost_per_second
        return cpu_cost + memory_cost + gpu_cost


class BudgetExceededError(Exception):
    pass
