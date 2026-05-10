from __future__ import annotations

import math
import time
from typing import Any

from pydantic import BaseModel

from backend.core.probability.prediction import Prediction
from backend.core.runtime.event_fabric.schema import SimHPCEvent
from backend.core.runtime.state_registry.service import WorldState
from backend.core.services.observability_service import observability
from backend.core.tracing import trace_context


class DecayProfile(BaseModel):
    """Per-regime decay configuration."""

    half_life_s: float
    uncertainty_growth: float = 0.3
    acceleration_factor: float = 1.0  # >1.0 = faster decay


class RegimeAwareDecayEngine:
    """Central engine with dynamic regime-aware acceleration."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._profiles: dict[str, DecayProfile] = {
                "normal": DecayProfile(half_life_s=86400.0, acceleration_factor=1.0),
                "panic": DecayProfile(half_life_s=14400.0, acceleration_factor=2.5),
                "disruption": DecayProfile(half_life_s=3600.0, acceleration_factor=4.0),
            }
        return cls._instance

    @classmethod
    def decay(cls) -> RegimeAwareDecayEngine:
        return cls()

    def apply(
        self,
        value: Any,
        uncertainty: float,
        base_half_life: float,
        last_updated: float,
        current_time: float,
        regime: str = "normal",
    ) -> tuple[Any, float]:
        """Apply regime-aware exponential decay."""
        if not isinstance(value, int | float):
            return value, uncertainty

        age = current_time - last_updated
        if age <= 0:
            return value, uncertainty

        profile = self._profiles.get(regime, self._profiles["normal"])

        # Effective half-life = base / regime acceleration
        effective_half_life = base_half_life / profile.acceleration_factor

        decay_factor = math.exp(-age / effective_half_life)
        decayed_value = value * decay_factor

        # Uncertainty grows faster in chaotic regimes
        uncertainty_boost = profile.uncertainty_growth * (1.0 - decay_factor)
        new_uncertainty = min(1.0, uncertainty + uncertainty_boost)

        return decayed_value, new_uncertainty

    async def propagate(self, state: WorldState, event: SimHPCEvent) -> WorldState:
        """Apply regime-aware decay across entire state."""
        with trace_context("temporal.decay.regime_aware"):
            obs = observability()
            obs.increment("regime_aware_decay_total")

            new_state = state.model_copy(deep=True)
            now = event.timestamp or time.time()
            regime = new_state.regime

            for _key, ent in new_state.entities.items():
                if hasattr(ent, "prediction") and isinstance(ent.prediction, Prediction):
                    decayed_value, new_unc = self.apply(
                        ent.prediction.value,
                        ent.prediction.uncertainty,
                        getattr(ent, "half_life_s", 86400.0),
                        ent.last_updated,
                        now,
                        regime,
                    )
                    ent.prediction.value = decayed_value
                    ent.prediction.uncertainty = new_unc
                    ent.last_updated = now

            # Log acceleration effect
            obs.gauge(
                "current_decay_acceleration",
                self._profiles.get(regime, self._profiles["normal"]).acceleration_factor,
            )

            return new_state
