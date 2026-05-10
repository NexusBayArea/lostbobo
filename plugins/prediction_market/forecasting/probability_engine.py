"""Probability engine — weighted ensemble with calibration and regime awareness."""

from __future__ import annotations

from typing import Any

from backend.core.probability.prediction import Prediction
from backend.core.runtime.state_registry.service import StateRegistryService
from backend.core.runtime.temporal.engine import TemporalEngine
from backend.plugins.prediction_market.forecasting.signals import ForecastSignal


class ProbabilityEngine:
    def __init__(self) -> None:
        self._temporal = TemporalEngine()
        self._state_registry = StateRegistryService.registry()

    async def forecast(
        self,
        signals: list[ForecastSignal],
        context: dict[str, Any] | None = None,
    ) -> Prediction:
        if not signals:
            return Prediction(
                value=0.5,
                confidence=0.0,
                uncertainty=1.0,
                provenance=[],
                metadata={"engine": "prediction_market_v1"},
            )

        regime = "normal"
        if context and "regime" in context:
            regime = context["regime"]
        elif self._state_registry:
            try:
                state = await self._state_registry.get_current()
                regime = getattr(state, "regime", "normal")
            except Exception:
                pass

        weighted_sum = sum(s.value * s.confidence for s in signals)
        total_weight = sum(s.confidence for s in signals)
        probability = weighted_sum / total_weight if total_weight else 0.5

        uncertainty = self._compute_uncertainty(signals, regime)

        if regime == "panic":
            uncertainty = min(1.0, uncertainty * 1.5)
        elif regime == "disruption":
            uncertainty = min(1.0, uncertainty * 2.0)

        confidence = 1.0 - uncertainty

        return Prediction(
            value=probability,
            confidence=confidence,
            uncertainty=uncertainty,
            provenance=[{"signal_id": s.id, "source": s.source} for s in signals],
            metadata={
                "engine": "prediction_market_v1",
                "regime": regime,
                "signal_count": len(signals),
                "total_weight": total_weight,
            },
        )

    def _compute_uncertainty(self, signals: list[ForecastSignal], regime: str) -> float:
        if len(signals) <= 1:
            base = 0.3
        else:
            values = [s.value for s in signals]
            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            std_dev = variance**0.5
            disagreement = std_dev

            confidence_scores = [s.confidence for s in signals]
            avg_confidence = sum(confidence_scores) / len(confidence_scores)

            disagreement_factor = disagreement * 0.7
            confidence_factor = (1.0 - avg_confidence) * 0.3
            base = disagreement_factor + confidence_factor

        if regime == "disruption":
            base = min(1.0, base * 1.5)
        elif regime == "panic":
            base = min(1.0, base * 1.2)

        return min(1.0, max(0.0, base))
