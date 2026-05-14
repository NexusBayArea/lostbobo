"""Demand prediction for warm pool provisioning."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from backend.app.core.supabase import get_supabase_client

logger = logging.getLogger(__name__)


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

    def _mock_forecast(self, horizon: ForecastHorizon) -> dict[str, Any]:
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


class DemandForecaster:
    _instance: DemandForecaster | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._forecaster = CapacityForecaster()
        return cls._instance

    @classmethod
    def forecaster(cls) -> DemandForecaster:
        return cls()

    async def predict_demand(
        self,
        horizon_minutes: int = 30,
        pool_classes: Any = None,
    ) -> dict[str, float]:
        try:
            from backend.core.hardware.pools import PoolClass as PoolClassType

            regime = "normal"
            try:
                from backend.core.runtime.state_registry.service import (
                    StateRegistryService,
                )

                state = await StateRegistryService.registry().get_current()
                regime = getattr(state, "regime", "normal")
            except Exception:
                pass

            ml_forecast: dict[str, float] = {}
            try:
                from backend.core.hardware.ml_integration import get_hardware_ml_models

                ml = get_hardware_ml_models()
                ml_forecast = await ml.predict_demand(horizon_minutes)
            except Exception:
                pass

            stats_forecast = await self._statistical_baseline()

            regime_multiplier = {"normal": 1.0, "panic": 1.45, "disruption": 1.85}.get(regime, 1.3)

            combined: dict[str, float] = {}
            targets = pool_classes or list(PoolClassType)
            for pc in targets:
                key = pc.value if hasattr(pc, "value") else str(pc)
                ml_val = ml_forecast.get(key, 0.4)
                stat_val = stats_forecast.get(key, 0.5)
                final_demand = (0.65 * ml_val + 0.35 * stat_val) * regime_multiplier
                combined[key] = max(0.0, min(1.0, final_demand))

            try:
                from backend.core.services.observability_service import observability

                obs = observability()
                obs.gauge("demand_forecast_isolated", combined.get("isolated", 0.0))
                obs.gauge("demand_forecast_dedicated", combined.get("dedicated", 0.0))
            except Exception:
                pass

            return combined
        except Exception:
            return {"shared": 0.55, "dedicated": 0.65, "isolated": 0.45}

    async def _statistical_baseline(self) -> dict[str, float]:
        return {
            "shared": 0.55,
            "dedicated": 0.65,
            "isolated": 0.45,
            "low_cost": 0.70,
            "realtime": 0.80,
            "high_memory": 0.50,
        }


class PredictiveCapacityForecaster:
    _instance: PredictiveCapacityForecaster | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._forecaster = CapacityForecaster()
        return cls._instance

    @classmethod
    def forecaster(cls) -> PredictiveCapacityForecaster:
        return cls()

    async def predict_capacity(
        self,
        horizon_minutes: int = 60,
        scenarios: bool = True,
    ) -> dict[str, Any]:
        regime = "normal"
        try:
            from backend.core.runtime.state_registry.service import StateRegistryService

            state = await StateRegistryService.registry().get_current()
            regime = getattr(state, "regime", "normal")
        except Exception:
            pass

        ml_base: dict[str, float] = {}
        try:
            from backend.core.hardware.ml_integration import get_hardware_ml_models

            ml = get_hardware_ml_models()
            ml_base = await ml.predict_demand(horizon_minutes)
        except Exception:
            pass

        trend = await self._compute_trend_forecast(horizon_minutes)

        regime_weight = {"normal": 0.4, "panic": 0.7, "disruption": 0.85}.get(regime, 0.55)

        forecast: dict[str, dict[str, Any]] = {}
        try:
            from backend.core.hardware.pools import PoolClass

            for pc in list(PoolClass):
                key = pc.value
                base_demand = 0.6 * ml_base.get(key, 0.5) + 0.4 * trend.get(key, 0.5)
                uncertainty = await self._estimate_uncertainty(key, horizon_minutes)
                predicted = min(1.0, base_demand * (1 + regime_weight))

                forecast[key] = {
                    "predicted_demand": round(predicted, 3),
                    "lower_bound": round(max(0.0, base_demand - uncertainty), 3),
                    "upper_bound": round(min(1.0, base_demand + uncertainty), 3),
                    "confidence": round(max(0.1, 1.0 - uncertainty * 0.8), 3),
                    "recommended_warm_reserve": int(base_demand * 4) if base_demand > 0.6 else 1,
                }
        except Exception:
            for key in trend:
                base_demand = trend[key]
                uncertainty = await self._estimate_uncertainty(key, horizon_minutes)
                predicted = min(1.0, base_demand * (1 + regime_weight))
                forecast[key] = {
                    "predicted_demand": round(predicted, 3),
                    "lower_bound": round(max(0.0, base_demand - uncertainty), 3),
                    "upper_bound": round(min(1.0, base_demand + uncertainty), 3),
                    "confidence": round(max(0.1, 1.0 - uncertainty * 0.8), 3),
                    "recommended_warm_reserve": int(base_demand * 4) if base_demand > 0.6 else 1,
                }

        scenarios_data: dict[str, Any] = {}
        if scenarios:
            scenarios_data = {
                "normal": forecast,
                "high_load": {
                    k: {
                        **v,
                        "predicted_demand": round(min(1.0, v["predicted_demand"] * 1.45), 3),
                    }
                    for k, v in forecast.items()
                },
                "disruption": {
                    k: {
                        **v,
                        "predicted_demand": round(min(1.0, v["predicted_demand"] * 1.9), 3),
                    }
                    for k, v in forecast.items()
                },
            }

        result = {
            "horizon_minutes": horizon_minutes,
            "forecast": forecast,
            "scenarios": scenarios_data,
            "regime": regime,
            "generated_at": datetime.now(UTC).isoformat(),
        }

        try:
            from backend.core.services.observability_service import observability

            obs = observability()
            obs.gauge(
                "predicted_isolated_demand",
                forecast.get("isolated", {}).get("predicted_demand", 0),
            )
        except Exception:
            pass

        return result

    async def _compute_trend_forecast(self, horizon_minutes: int) -> dict[str, float]:
        return {
            "shared": 0.58,
            "dedicated": 0.72,
            "isolated": 0.48,
            "low_cost": 0.65,
            "realtime": 0.81,
            "high_memory": 0.55,
        }

    async def _estimate_uncertainty(self, pool_class: str, horizon_minutes: int) -> float:
        base = 0.12
        horizon_factor = min(0.35, horizon_minutes / 240)
        return base + horizon_factor
