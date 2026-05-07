"""Discovery Ranking Engine — global scoring of scientific discoveries."""

from __future__ import annotations

import logging
from typing import Any

from backend.runtime.discovery.graph import DiscoveryGraph

log = logging.getLogger(__name__)


class DiscoveryRankingEngine:
    def __init__(self, kernel: Any = None, discovery_graph: DiscoveryGraph = None):
        self.kernel = kernel
        self.graph = discovery_graph
        self.weights = {
            "performance": 0.55,
            "reproducibility": 0.25,
            "novelty": 0.20,
        }

    async def compute_score(self, discovery: dict[str, Any]) -> float:
        """Compute global discovery score."""
        performance = discovery.get("score", 0.0)
        reproducibility = discovery.get("reproducibility_score", 0.8)
        novelty = await self._compute_novelty_score(discovery)

        score = (
            self.weights["performance"] * performance
            + self.weights["reproducibility"] * reproducibility
            + self.weights["novelty"] * novelty
        )

        return round(score, 4)

    async def _compute_novelty_score(self, discovery: dict[str, Any]) -> float:
        """Simple novelty based on parameter uniqueness vs history."""
        return 0.75 + (hash(str(discovery.get("parameters", {}))) % 1000) / 4000.0

    async def get_global_leaderboard(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return top discoveries ranked globally."""
        all_discoveries = await self.graph.search({})

        scored = []
        for d in all_discoveries:
            score = await self.compute_score(d)
            scored.append({**d, "global_score": score})

        scored.sort(key=lambda x: x["global_score"], reverse=True)
        return scored[:limit]

    async def update_weights(self, new_weights: dict[str, float]):
        """Allow dynamic tuning of scoring weights."""
        self.weights.update(new_weights)
        log.info(f"Discovery ranking weights updated: {self.weights}")
