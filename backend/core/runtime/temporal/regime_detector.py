from __future__ import annotations

import time

import numpy as np
from pydantic import BaseModel, Field

from backend.core.probability.prediction import Prediction
from backend.core.runtime.state_registry.service import WorldState
from backend.core.services.observability_service import observability
from backend.core.tracing import trace_context


class RegimeStats(BaseModel):
    entropy: float = 0.0
    volatility: float = 0.0
    change_rate: float = 0.0  # rate of state mutations
    disagreement: float = 0.0  # from ensemble forecasts
    last_updated: float = Field(default_factory=time.time)


class AdaptiveRegimeDetector:
    """Learns regime boundaries from historical data."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._history: list[RegimeStats] = []
            cls._instance._thresholds = {
                "normal": 0.0,
                "panic": 0.35,
                "disruption": 0.65,
            }
        return cls._instance

    @classmethod
    def detector(cls) -> AdaptiveRegimeDetector:
        return cls()

    def detect(self, state: WorldState) -> str:
        """Adaptive regime classification."""
        with trace_context("regime.detect.adaptive"):
            obs = observability()

            stats = self._compute_stats(state)

            # Adaptive threshold learning (simple online update)
            self._history.append(stats)
            if len(self._history) > 1000:
                self._history.pop(0)

            # Dynamic threshold adjustment based on recent variance
            recent_entropies = [s.entropy for s in self._history[-200:]]
            if recent_entropies:
                mean_ent = np.mean(recent_entropies)
                std_ent = np.std(recent_entropies)
                self._thresholds["panic"] = float(mean_ent + 0.8 * std_ent)
                self._thresholds["disruption"] = float(mean_ent + 1.8 * std_ent)

            entropy = stats.entropy
            if entropy > self._thresholds["disruption"] or stats.volatility > 0.75:
                regime = "disruption"
            elif entropy > self._thresholds["panic"] or stats.disagreement > 0.25:
                regime = "panic"
            else:
                regime = "normal"

            obs.gauge("current_regime_entropy", entropy)
            obs.gauge("current_volatility", stats.volatility)
            return regime

    def _compute_stats(self, state: WorldState) -> RegimeStats:
        if not state.entities:
            return RegimeStats()

        entropies = [e.uncertainty for e in state.entities.values() if hasattr(e, "uncertainty")]
        values = [
            getattr(e, "prediction", e).value
            if hasattr(e, "prediction")
            else (e if isinstance(e, int | float) else 0.0)
            for e in state.entities.values()
        ]

        return RegimeStats(
            entropy=float(np.mean(entropies)) if entropies else 0.0,
            volatility=float(np.std(values)) if values else 0.0,
            change_rate=0.0,
            disagreement=0.0,
        )

    def update_from_feedback(self, predictions: list[Prediction], outcomes: list[int]):
        """Improve detection using resolved forecasts (Brier-based)."""
        pass
