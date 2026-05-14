from __future__ import annotations

from typing import Any

from backend.core.runtime.forecast import ForecastResult, ProbabilisticForecastModel


class WildfireModel(ProbabilisticForecastModel):
    async def predict(self, payload: dict[str, Any]) -> ForecastResult:
        region = payload.get("region")
        season = payload.get("season", "dry")
        return ForecastResult(
            mean=0.15,
            confidence_interval=(0.05, 0.35),
            metadata={
                "region": region,
                "season": season,
                "risk_index": 0.15,
                "fuel_moisture_pct": 12.0,
            },
        )
