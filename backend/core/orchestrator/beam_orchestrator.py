"""Beam Orchestrator with Redis Real-Time Streaming."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from backend.core.models.hypothesis import Hypothesis
from backend.core.redis.beam_streamer import BeamStreamer
from backend.runtime.rag.router import RAGRouter

log = logging.getLogger(__name__)


class BeamOrchestrator:
    def __init__(self, agents: list, sim_runner, rag: RAGRouter, config: dict[str, Any]):
        self.agents = agents
        self.sim_runner = sim_runner
        self.rag = rag
        self.config = config
        self.streamer = BeamStreamer()

    async def run(self, query: str, tenant_id: str = "public", request_id: str | None = None) -> Hypothesis:
        await self.streamer.connect()

        if not request_id:
            request_id = f"req_{int(time.time()*1000)}"

        beams: list[Hypothesis] = await self._generate_initial_beams(query, tenant_id)

        for stage in self.config.get("stages", ["plausibility", "rag", "simulation", "robustness"]):
            beams = await self._run_stage(beams, stage, tenant_id)
            beams = self._prune(beams)
            await self.streamer.rerank_and_notify(request_id, beams)

            if self._should_early_exit(beams):
                break

        winner = max(beams, key=lambda h: h.trust_score)
        winner.stage = "complete"
        await self.streamer.publish_hypothesis(winner, request_id)
        return winner

    async def _generate_initial_beams(self, query: str, tenant_id: str) -> list[Hypothesis]:
        context = await self.rag.retrieve(query, tenant_id=tenant_id)
        beams = []
        for agent in self.agents:
            hypotheses = await agent.generate(query, context)
            beams.extend(hypotheses)
        return beams

    async def _run_stage(self, beams: list[Hypothesis], stage: str, tenant_id: str) -> list[Hypothesis]:
        if stage == "simulation" and self.sim_runner:
            return await asyncio.gather(*[self.sim_runner.run(h) for h in beams])
        return beams

    def _prune(self, beams: list[Hypothesis]) -> list[Hypothesis]:
        for h in beams:
            h.update_trust()
        beams.sort(key=lambda h: h.trust_score, reverse=True)
        return beams[: self.config.get("beam_width", 5)]

    def _should_early_exit(self, beams: list[Hypothesis]) -> bool:
        return bool(beams and beams[0].trust_score >= self.config.get("exit_threshold", 0.88))
