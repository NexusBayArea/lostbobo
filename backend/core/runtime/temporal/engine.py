"""Temporal engine — regime detection, exponential decay, and probabilistic propagation."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.core.runtime.event_fabric.schema import SimHPCEvent
    from backend.core.world_model.schema import WorldState


class RegimeDetector:
    def detect(self, state: WorldState) -> str:
        if not state.entities:
            return "normal"
        uncertainties = [e.uncertainty for e in state.entities.values()]
        avg_uncertainty = sum(uncertainties) / len(uncertainties)
        volatility = max(uncertainties) if uncertainties else 0.0
        if volatility > 0.7 or avg_uncertainty > 0.6:
            return "disruption"
        if volatility > 0.4 or avg_uncertainty > 0.35:
            return "panic"
        return "normal"


class TemporalEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._regime_detector = RegimeDetector()
        return cls._instance

    @classmethod
    def temporal(cls) -> TemporalEngine:
        return cls()

    async def propagate(self, state: WorldState, event: SimHPCEvent) -> WorldState:
        from backend.core.services.observability_service import observability
        from backend.core.services.tracing import tracer

        with tracer.start_as_current_span(
            "temporal.propagate",
            attributes={"event_type": event.event_type},
        ):
            obs = observability()
            obs.increment("temporal_propagations_total")

            new_state = state.model_copy(deep=True)
            now = event.timestamp

            for _key, ent in list(new_state.entities.items()):
                age = now - ent.last_updated
                if age > 0:
                    decay = math.exp(-age / max(1.0, ent.half_life_s))
                    if isinstance(ent.value, int | float):
                        ent.value = ent.value * decay
                    ent.uncertainty = min(1.0, ent.uncertainty * (2.0 - decay))
                    ent.last_updated = now

            new_regime = self._regime_detector.detect(new_state)
            if new_regime != new_state.regime:
                obs.increment("regime_shifts_total", {"from": new_state.regime, "to": new_regime})
                new_state.regime = new_regime
                if new_regime in ("panic", "disruption"):
                    for ent in new_state.entities.values():
                        ent.half_life_s = max(300.0, ent.half_life_s * 0.5)

            new_state = await self._propagate_uncertainty(new_state, event)

            obs.gauge(
                "current_regime_entropy",
                sum(e.uncertainty for e in new_state.entities.values()),
            )
            return new_state

    async def _propagate_uncertainty(self, state: WorldState, event: SimHPCEvent) -> WorldState:
        from backend.core.world_model.service import world_model_service

        try:
            return await world_model_service.propagate_uncertainty(state)
        except Exception:
            return state


def temporal_engine() -> TemporalEngine:
    return TemporalEngine()
