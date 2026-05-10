"""Policy-driven placement engine for governed execution reserves."""

from __future__ import annotations

from enum import Enum

from backend.core.hardware.pools import ExecutionCapacity, PoolClass
from backend.hardware.sla import SLATier


class PlacementPolicy(str, Enum):
    LOWEST_COST = "lowest_cost"
    LOWEST_LATENCY = "lowest_latency"
    ISOLATED = "isolated"
    HIGH_UTILIZATION = "high_utilization"
    ENERGY_EFFICIENT = "energy_efficient"


class PlacementEngine:
    async def select(
        self,
        candidates: list[ExecutionCapacity],
        request_policy: PlacementPolicy = PlacementPolicy.LOWEST_COST,
        sla_tier: SLATier | None = None,
    ) -> ExecutionCapacity | None:
        if not candidates:
            return None

        if sla_tier == SLATier.DEFENSE:
            return self._apply_isolated_policy(candidates)

        match request_policy:
            case PlacementPolicy.LOWEST_COST:
                return min(candidates, key=lambda c: c.hourly_cost_usd)
            case PlacementPolicy.LOWEST_LATENCY:
                return min(candidates, key=lambda c: c.metadata.get("latency_ms", float("inf")))
            case PlacementPolicy.HIGH_UTILIZATION:
                return min(candidates, key=lambda c: c.utilization_pct)
            case PlacementPolicy.ENERGY_EFFICIENT:
                return min(candidates, key=lambda c: c.metadata.get("power_watts", float("inf")))
            case _:
                return min(candidates, key=lambda c: c.hourly_cost_usd)

    def _apply_isolated_policy(
        self,
        candidates: list[ExecutionCapacity],
    ) -> ExecutionCapacity | None:
        isolated = [c for c in candidates if c.pool_class == PoolClass.ISOLATED]
        if not isolated:
            return None
        return min(isolated, key=lambda c: c.hourly_cost_usd)

    def rank_by_policy(
        self,
        candidates: list[ExecutionCapacity],
        policy: PlacementPolicy,
    ) -> list[ExecutionCapacity]:
        if not candidates:
            return []
        return sorted(candidates, key=lambda c: self._score(c, policy))

    def _score(self, cap: ExecutionCapacity, policy: PlacementPolicy) -> float:
        match policy:
            case PlacementPolicy.LOWEST_COST:
                return cap.hourly_cost_usd
            case PlacementPolicy.LOWEST_LATENCY:
                return cap.metadata.get("latency_ms", 9999.0)
            case PlacementPolicy.HIGH_UTILIZATION:
                return -cap.utilization_pct
            case PlacementPolicy.ENERGY_EFFICIENT:
                return cap.metadata.get("power_watts", 9999.0)
            case _:
                return cap.hourly_cost_usd


_engine: PlacementEngine | None = None


def get_placement_engine() -> PlacementEngine:
    global _engine
    if _engine is None:
        _engine = PlacementEngine()
    return _engine
