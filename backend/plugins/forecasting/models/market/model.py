from __future__ import annotations

from typing import Any

from backend.core.runtime.forecast import ForecastResult, ProbabilisticForecastModel


class MarketModel(ProbabilisticForecastModel):
    async def predict(self, payload: dict[str, Any]) -> ForecastResult:
        symbol = payload.get("symbol")
        horizon = payload.get("horizon", "30d")
        return ForecastResult(
            mean=0.02,
            confidence_interval=(-0.05, 0.09),
            metadata={
                "symbol": symbol,
                "horizon": horizon,
                "volatility": 0.25,
            },
        )
