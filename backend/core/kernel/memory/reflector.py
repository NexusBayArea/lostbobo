"""Reflector — updates beliefs, world model, and policies from observations."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from backend.core.kernel.kernel import Kernel

from backend.core.kernel.memory.observational import Observation

log = logging.getLogger(__name__)


class Reflector:
    """Periodic / triggered reflection that updates persistent state."""

    def __init__(self, kernel: Kernel):
        self.kernel = kernel

    async def reflect(self, observations: list[Observation]) -> dict[str, Any]:
        """Update world model + beliefs based on new observations."""
        if not observations:
            return {"status": "no_observations"}

        aggregated = {
            "new_beliefs": [obs.insight for obs in observations],
            "avg_confidence": sum(o.confidence for o in observations) / len(observations),
        }

        await self.kernel.execute(
            {
                "type": "WORLD_UPDATE",
                "payload": {
                    "entity": "belief_system",
                    "variable": "recent_insights",
                    "value": aggregated["avg_confidence"],
                    "uncertainty": {"mean": aggregated["avg_confidence"], "std": 0.1},
                },
            }
        )

        log.info("Reflector updated beliefs from %d observations", len(observations))
        return aggregated
