"""Bridge to existing conformal prediction system."""

from __future__ import annotations

import numpy as np


class ConformaBridge:
    def __init__(self, coverage: float = 0.90):
        self.coverage = coverage
        self._alpha = 1.0 - coverage
        self._cal_scores: list[float] = []

    def get_interval(self, point_estimate: float, coverage: float | None = None) -> tuple[float, float]:
        """Simple fallback until full conformal.py integration."""
        radius = 0.20 if len(self._cal_scores) < 30 else 0.12
        return (
            float(np.clip(point_estimate - radius, 0.0, 1.0)),
            float(np.clip(point_estimate + radius, 0.0, 1.0)),
        )

    def update(
        self, predicted_prob: float, actual_outcome: float, question_id: str, category: str | None = None
    ) -> float:
        score = abs(actual_outcome - predicted_prob)
        self._cal_scores.append(score)
        return score
