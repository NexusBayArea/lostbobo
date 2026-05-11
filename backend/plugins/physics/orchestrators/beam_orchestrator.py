from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from backend.core.certificate.service import CertificateService
from backend.core.models.hypothesis import Hypothesis
from backend.core.provenance.graph import ProvenanceGraph, ProvenanceNode
from backend.core.redis.beam_streamer import BeamStreamer
from backend.core.simulation.runner import SimulationRunner
from backend.plugins.physics.validation.library import PhysicsValidator
from backend.runtime.rag.router import RAGRouter

log = logging.getLogger(__name__)


class BeamOrchestrator:
    def __init__(
        self,
        agents: list | None = None,
        rag: RAGRouter | None = None,
        config: dict[str, Any] | None = None,
    ):
        self.agents = agents or []
        self.rag = rag
        self.config = config or {}
        self.sim_runner = SimulationRunner()
        self.streamer = BeamStreamer()
        self.provenance = ProvenanceGraph()
        self.certificate_service = CertificateService()
        self.validator = PhysicsValidator()

    async def run(self, query: str, tenant_id: str = "public", request_id: str | None = None) -> Hypothesis:
        # Pre-flight governance check
        from backend.core.kernel.kernel import SimHPCKernel

        kernel = SimHPCKernel()

        await kernel.execute(
            {
                "type": "GOVERNANCE_CHECK",
                "payload": {
                    "operation": "llm",
                    "estimated_tokens": 800,  # adjust dynamically
                    "tenant_id": tenant_id,
                    "user_id": "current_user",
                },
            }
        )

        await self.streamer.connect()

        if not request_id:
            request_id = f"req_{int(time.time() * 1000)}"

        beams: list[Hypothesis] = await self._generate_initial_beams(query, tenant_id)

        for stage in self.config.get("stages", ["plausibility", "rag", "simulation", "robustness"]):
            beams = await self._run_stage(beams, stage, tenant_id)
            beams = self._prune(beams)
            await self.streamer.rerank_and_notify(request_id, beams)

            if self._should_early_exit(beams):
                log.info("Early exit at stage %s", stage)
                break

        winner = max(beams, key=lambda h: h.trust_score)
        winner.stage = "complete"

        # NEW: Physics Validation
        sim_result = await self.sim_runner.run(winner)
        winner = sim_result.hypothesis
        val = self.validator.validate(winner, sim_result.data)
        if val.passed:
            winner.trust_score = min(0.98, winner.trust_score * 1.15)
            winner.stage = "physics_validated"

        await self.provenance.add_node(
            ProvenanceNode(
                node_id=winner.id,
                node_type="final_hypothesis",
                data={"query": query, "validation": val.__dict__},
                parent_ids=[],
                timestamp=time.time(),
            )
        )

        await self.certificate_service.issue(winner)

        await self.streamer.publish_hypothesis(winner, request_id)
        return winner

    async def _generate_initial_beams(self, query: str, tenant_id: str) -> list[Hypothesis]:
        context = {}
        if self.rag:
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
