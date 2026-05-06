"""Simulation Runner — bridges Hypothesis to actual SimHPC execution."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from backend.core.models.hypothesis import Hypothesis
from backend.core.robustness.check import RobustnessCheck
from backend.runtime.cache.simulation_cache import SimulationCache
from backend.runtime.provenance.graph import ProvenanceGraph, ProvenanceNode

log = logging.getLogger(__name__)


class SimulationRunner:
    def __init__(self):
        self.cache = SimulationCache()
        self.graph = ProvenanceGraph()

    async def run(self, h: Hypothesis) -> Hypothesis:
        """Execute simulation for a Hypothesis and update scores."""
        start = time.time()

        cached = await self.cache.get(h.sim_params)
        if cached:
            log.info("Cache hit for hypothesis %s", h.id)
            h.sim_result = cached
            h.simulation_score = cached.get("agreement_score", 0.85)
            h.stage = "simulation_cached"
            return h

        sim_result = await self._execute_simulation(h.sim_params)

        h.sim_result = sim_result
        h.simulation_score = sim_result.get("agreement_score", 0.75)
        h.stage = "simulation"

        h = RobustnessCheck.run(h)

        await self.cache.store(h.sim_params, sim_result)

        node = ProvenanceNode(
            node_id=h.id,
            node_type="simulation",
            data={"sim_params": h.sim_params, "result": sim_result},
        )
        await self.graph.add_node(node)

        log.info(
            "Simulation completed for %s in %.2fs (score: %.3f)",
            h.id,
            time.time() - start,
            h.simulation_score,
        )

        return h

    async def _execute_simulation(self, params: dict[str, Any]) -> dict[str, Any]:
        """Real simulation stub — replace with PyBaMM / MFEM / SUNDIALS call."""
        await asyncio.sleep(0.3)

        return {
            "agreement_score": 0.88,
            "max_temperature": 335.2,
            "plating_probability": 0.42,
            "capacity_fade": 0.07,
            "solver_converged": True,
            "runtime_seconds": 0.3,
        }
