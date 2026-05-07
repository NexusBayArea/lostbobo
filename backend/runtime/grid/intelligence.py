"""Experiment Intelligence — meta-learning across experiments."""

from __future__ import annotations

import logging
from typing import Any

from backend.runtime.discovery.graph import DiscoveryGraph

log = logging.getLogger(__name__)


class ExperimentIntelligence:
    def __init__(self, kernel: Any = None, discovery_graph: DiscoveryGraph = None):
        self.kernel = kernel
        self.graph = discovery_graph

    async def get_parameter_priors(self, objective: str, domain: str = "general") -> dict[str, Any]:
        """Cross-experiment parameter priors from similar past discoveries."""
        history = await self.graph.search({"objective": objective, "domain": domain, "score_gt": 0.7})

        priors = {}
        for disc in history:
            params = disc.get("parameters", {})
            for k, v in params.items():
                if k not in priors:
                    priors[k] = []
                priors[k].append(v)

        result = {}
        for k, values in priors.items():
            if values:
                mean = sum(values) / len(values)
                result[k] = {
                    "mean": mean,
                    "std": (max(values) - min(values)) / 4,
                    "suggested_range": [min(values), max(values)],
                    "source_count": len(values),
                }

        log.info(f"Generated priors for {objective} from {len(history)} past experiments")
        return result

    async def suggest_next_swarm(self, experiment_id: str, objective: str = "general") -> dict[str, Any]:
        """Propose next swarm configuration using cross-experiment learning."""
        priors = await self.get_parameter_priors(objective)

        return {
            "suggested_algorithm": "bayesian",
            "parameter_priors": priors,
            "recommended_swarm_size": 1500 + len(priors) * 200,
            "focus_areas": list(priors.keys())[:5],
            "confidence": 0.82,
        }
