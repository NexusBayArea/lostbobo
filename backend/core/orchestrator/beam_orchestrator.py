"""Beam Orchestrator — controls speculative multi-path reasoning with Hypothesis."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from backend.core.models.hypothesis import Hypothesis
from backend.runtime.rag.router import RAGRouter

log = logging.getLogger(__name__)


class BeamOrchestrator:
    def __init__(self, agents: list, sim_runner, rag: RAGRouter, config: dict[str, Any]):
        self.agents = agents
        self.sim_runner = sim_runner
        self.rag = rag
        self.config = config

    async def run(self, query: str, tenant_id: str = "public") -> Hypothesis:
        """Main entrypoint."""
        beams: list[Hypothesis] = await self._generate_initial_beams(query, tenant_id)

        for stage in self.config.get("stages", ["plausibility", "rag", "simulation", "robustness"]):
            beams = await self._run_stage(beams, stage, tenant_id)
            beams = self._prune(beams)

            if self._should_early_exit(beams):
                log.info(f"Early exit at {stage} with trust {beams[0].trust_score:.3f}")
                break

        winner = max(beams, key=lambda h: h.trust_score)
        winner.stage = "complete"
        return winner

    async def _generate_initial_beams(self, query: str, tenant_id: str) -> list[Hypothesis]:
        context = await self.rag.retrieve(query, tenant_id=tenant_id)
        beams = []
        for agent in self.agents:
            hypotheses = await agent.generate(query, context)
            beams.extend(hypotheses)
        return beams

    async def _run_stage(self, beams: list[Hypothesis], stage: str, tenant_id: str) -> list[Hypothesis]:
        if stage == "simulation":
            return await asyncio.gather(*[self.sim_runner.run(h) for h in beams])
        return beams

    def _prune(self, beams: list[Hypothesis]) -> list[Hypothesis]:
        for h in beams:
            h.update_trust()
        beams.sort(key=lambda h: h.trust_score, reverse=True)
        return beams[: self.config.get("beam_width", 5)]

    def _should_early_exit(self, beams: list[Hypothesis]) -> bool:
        return bool(beams and beams[0].trust_score >= self.config.get("exit_threshold", 0.88))
