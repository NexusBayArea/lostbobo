"""WorldService — Kernel-managed probabilistic world model."""

from __future__ import annotations

import logging
from typing import Any

from backend.core.kernel.state.world_state import WorldState
from backend.core.memory.service import MemoryService
from backend.core.redis.beam_streamer import BeamStreamer

log = logging.getLogger(__name__)


class WorldService:
    def __init__(self, state: WorldState):
        self.state = state
        self.memory = MemoryService()
        self.streamer = BeamStreamer()

    async def update(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Update world state through Kernel."""
        self.state.apply_update(payload)

        await self.streamer._publish_event(
            f"world_{self.state.state_id}",
            {
                "event": "world_updated",
                "state_id": self.state.state_id,
                "timestamp": self.state.timestamp.isoformat(),
            },
        )

        log.info("World updated: %s", self.state.state_id)
        return self.state.snapshot()

    async def simulate(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Trigger simulation skill through Kernel."""
        return {"status": "simulation_triggered", "payload_for_kernel": payload}

    async def propagate_uncertainty(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Monte-Carlo uncertainty propagation."""
        results = {}
        for entity, vars_dict in self.state.entities.items():
            for var_name, var in vars_dict.items():
                mean = var.value
                std = var.uncertainty.std or (mean * 0.1)
                results[f"{entity}.{var_name}"] = {
                    "mean": mean,
                    "std": std,
                    "p10": mean - 1.28 * std,
                    "p90": mean + 1.28 * std,
                }
        return results
