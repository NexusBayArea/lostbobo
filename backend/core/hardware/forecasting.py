"""Demand prediction for warm pool provisioning."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from backend.app.core.supabase import get_supabase_client


class ForecastHorizon(str, Enum):
    MINUTES_15 = "15m"
    HOUR_1 = "1h"
    HOURS_4 = "4h"
    HOURS_24 = "24h"


@dataclass
class PoolClassForecast:
    pool_class: str
    horizon: ForecastHorizon
    predicted_demand: int
    current_warm: int
    shortfall: int
    confidence_pct: float
    recommended_provisions: int


@dataclass
class DemandSnapshot:
    snapshot_id: str
    tenant_id: str
    sla_tier: str
    pool_class: str
    queued_jobs: int
    active_simulations: int
    predicted_demand_15m: int
    timestamp: str


class CapacityForecaster:
    def __init__(self) -> None:
        self._db = get_supabase_client()

    async def predict_demand(
        self,
        horizon: ForecastHorizon = ForecastHorizon.MINUTES_15,
    ) -> dict[str, Any]:
        if self._db is None:
            return self._mock_forecast(horizon)

        result = self._db.table("simulation_runs").select("sla_tier, status").eq("status", "queued").execute()

        queued_by_tier: dict[str, int] = {}
        for row in result.data or []:
            tier = row.get("sla_tier", "free")
            queued_by_tier[tier] = queued_by_tier.get(tier, 0) + 1

        active = self._db.table("simulation_runs").select("id").eq("status", "running").execute()
        active_count = len(active.data or [])

        forecasts: list[dict[str, Any]] = []
        for tier, count in queued_by_tier.items():
            shortfall = max(0, count - 2)
            forecasts.append(
                {
                    "sla_tier": tier,
                    "predicted_demand": count,
                    "current_warm": 2,
                    "shortfall": shortfall,
                    "recommended_provisions": shortfall,
                    "confidence_pct": 75.0,
                }
            )

        return {
            "horizon": horizon.value,
            "forecasts": forecasts,
            "total_queued": sum(queued_by_tier.values()),
            "active_simulations": active_count,
            "predicted_at": datetime.now(UTC).isoformat(),
        }

    def _mock_forecast(
        self,
        horizon: ForecastHorizon,
    ) -> dict[str, Any]:
        return {
            "horizon": horizon.value,
            "forecasts": [],
            "total_queued": 0,
            "active_simulations": 0,
            "predicted_at": datetime.now(UTC).isoformat(),
        }

    async def record_snapshot(
        self,
        tenant_id: str,
        sla_tier: str,
        pool_class: str,
        queued_jobs: int,
        active_simulations: int,
    ) -> None:
        snapshot = DemandSnapshot(
            snapshot_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            sla_tier=sla_tier,
            pool_class=pool_class,
            queued_jobs=queued_jobs,
            active_simulations=active_simulations,
            predicted_demand_15m=queued_jobs,
            timestamp=datetime.now(UTC).isoformat(),
        )
        if self._db is None:
            return
        self._db.table("capacity_forecasting_snapshots").insert(
            {
                "snapshot_id": snapshot.snapshot_id,
                "tenant_id": snapshot.tenant_id,
                "sla_tier": snapshot.sla_tier,
                "pool_class": snapshot.pool_class,
                "queued_jobs": snapshot.queued_jobs,
                "active_simulations": snapshot.active_simulations,
                "predicted_demand_15m": snapshot.predicted_demand_15m,
                "timestamp": snapshot.timestamp,
            }
        ).execute()


_forecaster: CapacityForecaster | None = None


def get_capacity_forecaster() -> CapacityForecaster:
    global _forecaster
    if _forecaster is None:
        _forecaster = CapacityForecaster()
    return _forecaster
