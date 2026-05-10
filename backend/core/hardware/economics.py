"""Margin & cost optimization for hardware execution."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from backend.core.hardware.pools import ExecutionCapacity
    from backend.hardware.scheduler import SchedulingRequest

from backend.hardware.reservations import WHOLESALE_COST_MULTIPLIER

logger = logging.getLogger(__name__)


class CostModel(str, Enum):
    ON_DEMAND = "on_demand"
    SPOT = "spot"
    RESERVED_1M = "reserved_1m"
    RESERVED_3M = "reserved_3m"
    RESERVED_1Y = "reserved_1y"
    DEDICATED = "dedicated"


@dataclass
class NodeEconomics:
    node_id: str
    provider: str
    gpu_type: str
    gpu_count: int
    cost_model: CostModel
    retail_hourly_usd: float
    wholesale_hourly_usd: float
    simhpc_margin_usd: float
    utilization_pct: float = 0.0
    estimated_monthly_revenue: float = 0.0
    estimated_monthly_cost: float = 0.0
    net_margin_usd: float = 0.0


@dataclass
class EconomicScore:
    margin: float
    utilization_boost: float
    sla_compliance: float
    latency_penalty: float
    demand_bonus: float
    total_score: float
    recommended_action: str


class EconomicsEngine:
    def compute_node_economics(
        self,
        node_id: str,
        provider: str,
        gpu_type: str,
        gpu_count: int,
        retail_hourly_usd: float,
        cost_model: CostModel = CostModel.ON_DEMAND,
        utilization_pct: float = 0.0,
    ) -> NodeEconomics:
        wholesale = retail_hourly_usd * WHOLESALE_COST_MULTIPLIER
        simhpc_margin = retail_hourly_usd - wholesale
        hours_per_month = 730
        estimated_monthly_revenue = retail_hourly_usd * gpu_count * hours_per_month * (utilization_pct / 100)
        estimated_monthly_cost = wholesale * gpu_count * hours_per_month
        net_margin = estimated_monthly_revenue - estimated_monthly_cost

        return NodeEconomics(
            node_id=node_id,
            provider=provider,
            gpu_type=gpu_type,
            gpu_count=gpu_count,
            cost_model=cost_model,
            retail_hourly_usd=retail_hourly_usd,
            wholesale_hourly_usd=wholesale,
            simhpc_margin_usd=simhpc_margin,
            utilization_pct=utilization_pct,
            estimated_monthly_revenue=round(estimated_monthly_revenue, 2),
            estimated_monthly_cost=round(estimated_monthly_cost, 2),
            net_margin_usd=round(net_margin, 2),
        )

    def compute_total_margin(self, nodes: list[NodeEconomics]) -> dict[str, Any]:
        total_revenue = sum(n.estimated_monthly_revenue for n in nodes)
        total_cost = sum(n.estimated_monthly_cost for n in nodes)
        total_margin = sum(n.net_margin_usd for n in nodes)
        by_provider: dict[str, float] = {}
        for n in nodes:
            by_provider[n.provider] = by_provider.get(n.provider, 0) + n.net_margin_usd

        return {
            "total_monthly_revenue_usd": round(total_revenue, 2),
            "total_monthly_cost_usd": round(total_cost, 2),
            "total_monthly_margin_usd": round(total_margin, 2),
            "margin_pct": round((total_margin / total_revenue * 100) if total_revenue else 0, 2),
            "by_provider": {k: round(v, 2) for k, v in by_provider.items()},
            "node_count": len(nodes),
        }

    def compute_spot_savings(
        self,
        on_demand_hourly: float,
        spot_hourly: float,
        gpu_count: int,
        hours: int,
    ) -> dict[str, Any]:
        on_demand_total = on_demand_hourly * gpu_count * hours
        spot_total = spot_hourly * gpu_count * hours
        savings = on_demand_total - spot_total
        return {
            "on_demand_total_usd": round(on_demand_total, 2),
            "spot_total_usd": round(spot_total, 2),
            "savings_usd": round(savings, 2),
            "savings_pct": round((savings / on_demand_total * 100) if on_demand_total else 0, 1),
        }

    def _get_tier_price(self, sla_tier: str, pool_class: str) -> float:
        pricing = {
            "free": {"shared": 0.0},
            "professional": {"shared": 0.45, "dedicated": 1.20},
            "enterprise": {"dedicated": 2.80, "isolated": 6.50},
            "defense": {"isolated": 18.0},
        }
        return pricing.get(sla_tier, {}).get(pool_class, 0.8)

    async def score_capacity(
        self,
        capacity: ExecutionCapacity,
        request: SchedulingRequest,
        predicted_demand: dict[str, float] | None = None,
    ) -> EconomicScore:
        base_cost = capacity.hourly_cost_usd * request.estimated_duration_minutes / 60
        price = self._get_tier_price(request.sla_tier.value, capacity.pool_class.value)
        margin = (price - base_cost) / price if price > 0 else 0.0
        utilization_boost = (1.0 - capacity.utilization_pct / 100) * 0.6
        sla_score = 1.0
        if request.sla_tier.value == "defense" and not capacity.itar_eligible:
            sla_score = 0.0
        elif request.sla_tier.value == "enterprise" and capacity.pool_class.value not in ("dedicated", "isolated"):
            sla_score = 0.4
        latency_requirement_ms = request.metadata.get("latency_requirement_ms", 800)
        latency_penalty = max(0.0, (latency_requirement_ms - 800) / 5000)
        demand_bonus = 0.0
        try:
            from backend.core.hardware.forecasting import DemandForecaster

            predicted = await DemandForecaster.forecaster().predict_demand(
                horizon_minutes=30,
                pool_classes=None,
            )
            if predicted and capacity.pool_class.value in predicted:
                demand_bonus = predicted[capacity.pool_class.value] * 0.28
        except Exception:
            pass
        total_score = (
            margin * 0.45 + utilization_boost * 0.20 + sla_score * 0.25 + demand_bonus * 0.10 - latency_penalty * 0.05
        )
        if margin > 0.42 and sla_score > 0.7:
            action = "reserve"
        elif margin < 0.15:
            action = "use_spot"
        else:
            action = "standard"
        score = EconomicScore(
            margin=margin,
            utilization_boost=utilization_boost,
            sla_compliance=sla_score,
            latency_penalty=latency_penalty,
            demand_bonus=demand_bonus,
            total_score=max(0.0, total_score),
            recommended_action=action,
        )
        try:
            from backend.core.services.observability_service import observability

            observability().gauge("economics_capacity_score", score.total_score)
        except Exception:
            pass
        return score

    async def optimize_allocation(
        self,
        request: SchedulingRequest,
        candidates: list[ExecutionCapacity],
    ) -> ExecutionCapacity | None:
        if not candidates:
            return None
        scored: list[tuple[float, ExecutionCapacity]] = []
        for cap in candidates:
            s = await self.score_capacity(cap, request)
            scored.append((s.total_score, cap))
        if not scored:
            return None
        return max(scored, key=lambda x: x[0])[1]


class ResourceEconomicsRuntime:
    _instance: ResourceEconomicsRuntime | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._engine = EconomicsEngine()
        return cls._instance

    @classmethod
    def economics(cls) -> ResourceEconomicsRuntime:
        return cls()

    def score_capacity(
        self,
        capacity: ExecutionCapacity,
        request: SchedulingRequest,
    ) -> EconomicScore:
        return self._engine.score_capacity(capacity, request)

    def optimize_allocation(
        self,
        request: SchedulingRequest,
        candidates: list[ExecutionCapacity],
    ) -> ExecutionCapacity | None:
        return self._engine.optimize_allocation(request, candidates)


_engine: EconomicsEngine | None = None


def get_economics_engine() -> EconomicsEngine:
    global _engine
    if _engine is None:
        _engine = EconomicsEngine()
    return _engine
