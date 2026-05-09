"""Temporal engine — regime detection and decay propagation."""

from __future__ import annotations

import logging
import time

from backend.core.runtime.event_fabric.schema import SimHPCEvent
from backend.core.world_model.schema import WorldState

log = logging.getLogger(__name__)


class TemporalEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._regime_thresholds = {
                "panic": 0.85,
                "disruption": 0.95,
            }
        return cls._instance

    async def propagate(self, world_state: WorldState, event: SimHPCEvent) -> WorldState:  # noqa: F821
        new_state = world_state.model_copy(deep=True)
        new_state.timestamp = event.timestamp

        await self._apply_decay(new_state)
        await self._detect_regime(new_state, event)

        return new_state

    async def _apply_decay(self, state: WorldState) -> None:
        now = time.time()
        for _key, entity in list(state.entities.items()):
            if hasattr(entity, "half_life_s"):
                elapsed = now - entity.last_updated
                decay = 0.5 ** (elapsed / entity.half_life_s)
                if hasattr(entity, "uncertainty"):
                    entity.uncertainty = min(1.0, entity.uncertainty * (1 + (1 - decay) * 0.1))

    async def _detect_regime(self, state: WorldState, event: SimHPCEvent) -> None:
        payload = event.payload or {}

        if payload.get("regime"):
            state.regime = payload["regime"]
            return

        uncertainty_vals = [u.mean for u in state.uncertainty.values() if hasattr(u, "mean")]
        if not uncertainty_vals:
            return

        max_unc = max(uncertainty_vals)
        if max_unc >= self._regime_thresholds["disruption"]:
            state.regime = "disruption"
        elif max_unc >= self._regime_thresholds["panic"]:
            state.regime = "panic"
        else:
            state.regime = "normal"


def temporal_engine() -> TemporalEngine:
    return TemporalEngine()
