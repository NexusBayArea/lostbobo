from __future__ import annotations

from typing import Any

from backend.core.runtime.forecast import ProbabilisticForecastModel, ForecastResult


class WeatherModel(ProbabilisticForecastModel):
    async def predict(self, payload: dict[str, Any]) -> ForecastResult:
        location = payload.get("location")
        horizon = payload.get("horizon", "7d")
        return ForecastResult(
            mean=22.5,
            confidence_interval=(18.0, 27.0),
            metadata={
                "location": location,
                "horizon": horizon,
                "temperature_celsius": 22.5,
                "precipitation_chance": 0.3,
            },
        )
