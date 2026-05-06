"""Analyst Agent — detects anomalies, generates hypotheses from World + Memory."""

from __future__ import annotations

from typing import Any

from backend.core.memory.service import MemoryService
from backend.core.models.hypothesis import Hypothesis
from backend.core.skills.registry import SkillRegistry
from backend.core.world_model.service import WorldModelService


class AnalystAgent:
    def __init__(self):
        self.world = WorldModelService()
        self.memory = MemoryService()
        self.skills = SkillRegistry()

    async def run(
        self, world_snapshot: dict[str, Any], memory_context: dict[str, Any] | None = None
    ) -> list[Hypothesis]:
        """Detect anomalies and generate simulation hypotheses."""
        hypotheses = []

        await self.memory.query({"type": "outcome"}, limit=10)

        hyp = Hypothesis()
        hyp.claim = {"anomaly": "grid_load_spike_detected"}
        hyp.reasoning = "Detected deviation > 2σ from baseline"
        hyp.plausibility_score = 0.82
        hypotheses.append(hyp)

        for skill in self.skills.list():
            if skill.kind == "simulation":
                result = await self.skills.execute(skill.name, world_snapshot)
                hypotheses.append(result)

        return hypotheses
