"""Governed execution reserve pools — warm capacity management."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from backend.hardware.sla import SLATier


class PoolClass(str, Enum):
    SHARED = "shared"
    DEDICATED = "dedicated"
    ISOLATED = "isolated"
    LOW_COST = "low_cost"
    REALTIME = "realtime"
    HIGH_MEMORY = "high_memory"


class ExecutionCapacity(BaseModel):
    id: str
    pool_class: PoolClass
    provider: str
    node_id: str
    gpu_type: str
    gpu_count: int
    status: str = "WARM_IDLE"
    tenant_id: str | None = None
    itar_eligible: bool = False
    attestation_id: str | None = None
    utilization_pct: float = 0.0
    hourly_cost_usd: float
    estimated_margin_usd: float = 0.0
    last_used: datetime | None = None
    warm_since: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class WarmPoolManager:
    def __init__(self) -> None:
        self._pools: dict[PoolClass, list[ExecutionCapacity]] = {c: [] for c in PoolClass}
        self._index: dict[str, ExecutionCapacity] = {}

    def register(self, capacity: ExecutionCapacity) -> None:
        self._pools[capacity.pool_class].append(capacity)
        self._index[capacity.id] = capacity

    def unregister(self, capacity_id: str) -> bool:
        cap = self._index.pop(capacity_id, None)
        if cap:
            self._pools[cap.pool_class].remove(cap)
            return True
        return False

    def by_pool_class(self, pool_class: PoolClass) -> list[ExecutionCapacity]:
        return list(self._pools.get(pool_class, []))

    def all_warm(self) -> list[ExecutionCapacity]:
        return [c for caps in self._pools.values() for c in caps if c.status == "WARM_IDLE"]

    async def get_warm_capacity(
        self,
        sla_tier: SLATier,
        pool_class: PoolClass,
        itar_required: bool = False,
        min_gpu_count: int = 1,
        region: str | None = None,
    ) -> ExecutionCapacity | None:
        candidates = self.all_warm()
        if itar_required:
            candidates = [c for c in candidates if c.itar_eligible]
        candidates = [c for c in candidates if c.gpu_count >= min_gpu_count]
        if region:
            candidates = [c for c in candidates if c.metadata.get("region", "") == region]
        if not candidates:
            return None
        if pool_class != PoolClass.SHARED:
            by_class = [c for c in candidates if c.pool_class == pool_class]
            if by_class:
                return min(by_class, key=lambda c: c.hourly_cost_usd)
        return min(candidates, key=lambda c: c.hourly_cost_usd)

    def reserve(self, capacity_id: str, tenant_id: str) -> bool:
        cap = self._index.get(capacity_id)
        if not cap or cap.status != "WARM_IDLE":
            return False
        cap.status = "RESERVED"
        cap.tenant_id = tenant_id
        return True

    def mark_running(self, capacity_id: str) -> None:
        cap = self._index.get(capacity_id)
        if cap:
            cap.status = "RUNNING"

    def release(self, capacity_id: str) -> bool:
        cap = self._index.get(capacity_id)
        if not cap:
            return False
        cap.status = "WARM_IDLE"
        cap.tenant_id = None
        cap.last_used = datetime.now(UTC)
        return True


_manager: WarmPoolManager | None = None


def get_warm_pool_manager() -> WarmPoolManager:
    global _manager
    if _manager is None:
        _manager = WarmPoolManager()
    return _manager
