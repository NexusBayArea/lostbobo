from __future__ import annotations

from typing import Any

import numpy as np
from pydantic import BaseModel, Field

from backend.core.runtime.state_registry.service import WorldState
from backend.core.services.observability_service import observability
from backend.core.tracing import trace_context


class RegimeForecast(BaseModel):
    """Probabilistic forecast of future regime."""

    predicted_regime: str
    probability: float
    confidence: float
    forecast_horizon_hours: float
    key_drivers: list[str]  # entropy, volatility, disagreement, ...
    metadata: dict[str, Any] = Field(default_factory=dict)


class PredictiveRegimeForecaster:
    """Forecasts regime transitions using historical patterns + ensemble signals."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._history: list[dict[str, Any]] = []
        return cls._instance

    @classmethod
    def forecaster(cls) -> PredictiveRegimeForecaster:
        return cls()

    async def forecast(self, state: WorldState, horizon_hours: float = 6.0) -> RegimeForecast:
        """Generate probabilistic regime forecast."""
        with trace_context("regime.forecast.predictive"):
            obs = observability()
            obs.increment("regime_forecasts_total")

            # Collect recent regime statistics (mocked for now)
            recent = self._get_recent_history(200)

            # Simple but effective predictors
            entropy_trend = self._compute_trend([s.get("entropy", 0.0) for s in recent])
            volatility_trend = self._compute_trend([s.get("volatility", 0.0) for s in recent])
            disagreement_trend = self._compute_trend([s.get("disagreement", 0.0) for s in recent])

            # Ensemble-based probability
            base_prob_disruption = 0.15 + 0.4 * entropy_trend + 0.35 * volatility_trend
            base_prob_panic = 0.35 + 0.25 * disagreement_trend

            # Normalize into probabilities
            probs = {
                "normal": max(0.0, 1.0 - base_prob_disruption - base_prob_panic),
                "panic": base_prob_panic,
                "disruption": base_prob_disruption,
            }
            total = sum(probs.values())
            probs = {k: v / total for k, v in probs.items()}

            predicted = max(probs, key=probs.get)

            forecast = RegimeForecast(
                predicted_regime=predicted,
                probability=probs[predicted],
                confidence=0.65 + 0.25 * (1.0 - abs(entropy_trend)),
                forecast_horizon_hours=horizon_hours,
                key_drivers=["entropy_trend", "volatility_trend", "disagreement_trend"],
                metadata={
                    "raw_probs": probs,
                    "trend_signals": {
                        "entropy": entropy_trend,
                        "volatility": volatility_trend,
                        "disagreement": disagreement_trend,
                    },
                },
            )

            obs.gauge("predicted_regime_prob", forecast.probability)
            return forecast

    def _compute_trend(self, values: list[float]) -> float:
        """Simple linear trend (-1.0 → +1.0)."""
        if len(values) < 5:
            return 0.0
        x = np.arange(len(values))
        y = np.array(values)
        slope = np.polyfit(x, y, 1)[0]
        return float(np.clip(slope * 10, -1.0, 1.0))  # normalized trend

    def _get_recent_history(self, limit: int) -> list[dict[str, Any]]:
        return self._history[-limit:]
