from __future__ import annotations

from typing import Any

from backend.core.runtime.forecast import ForecastResult, ProbabilisticForecastModel


class EVModel(ProbabilisticForecastModel):
    async def predict(self, payload: dict[str, Any]) -> ForecastResult:
        region = payload.get("region")
        horizon = payload.get("horizon", "5y")
        return ForecastResult(
            mean=0.35,
            confidence_interval=(0.25, 0.45),
            metadata={
                "region": region,
                "horizon": horizon,
                "adoption_rate": 0.35,
                "charging_demand_mw": 42.0,
            },
        )
