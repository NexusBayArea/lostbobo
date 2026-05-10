"""Margin & cost optimization for hardware execution."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from backend.hardware.reservations import WHOLESALE_COST_MULTIPLIER


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

    def compute_total_margin(
        self,
        nodes: list[NodeEconomics],
    ) -> dict[str, Any]:
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


_engine: EconomicsEngine | None = None


def get_economics_engine() -> EconomicsEngine:
    global _engine
    if _engine is None:
        _engine = EconomicsEngine()
    return _engine
