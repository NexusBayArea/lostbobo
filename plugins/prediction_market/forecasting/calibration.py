"""Ensemble calibration and market models."""

from __future__ import annotations

from typing import Any

from backend.core.probability.prediction import Prediction
from backend.plugins.prediction_market.forecasting.signals import ForecastSignal


class CalibrationAnalyzer:
    async def calibrate(
        self,
        predictions: list[Prediction],
        outcomes: list[float],
    ) -> dict[str, Any]:
        if not predictions or not outcomes:
            return {"calibration_error": 0.1, "n_samples": 0}

        errors = []
        for pred, outcome in zip(predictions, outcomes):
            errors.append(abs(pred.value - outcome))

        mean_error = sum(errors) / len(errors) if errors else 0.1
        return {
            "calibration_error": round(mean_error, 4),
            "n_samples": len(predictions),
            "brier_score": round(mean_error**2, 4),
        }

    async def compute_brier_score(
        self,
        predictions: list[Prediction],
        outcomes: list[float],
    ) -> float:
        if not predictions or not outcomes:
            return 0.25
        return sum((p.value - o) ** 2 for p, o in zip(predictions, outcomes)) / len(
            predictions
        )


class EnsembleBuilder:
    def build_ensemble(
        self,
        signals: list[ForecastSignal],
        weights: dict[str, float] | None = None,
    ) -> list[ForecastSignal]:
        if not weights:
            return signals
        return [s for s in signals if s.source in weights]

    def merge_signals(
        self,
        signal_groups: list[list[ForecastSignal]],
        weights: list[float],
    ) -> list[ForecastSignal]:
        result: list[ForecastSignal] = []
        for group, weight in zip(signal_groups, weights):
            for s in group:
                s.confidence = s.confidence * weight
                result.append(s)
        return result
