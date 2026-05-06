"""Planner Agent — evaluates actions, ranks strategies via simulation."""

from __future__ import annotations

from typing import Any

from backend.core.models.hypothesis import Hypothesis
from backend.core.skills.registry import SkillRegistry
from backend.core.world_model.service import WorldModelService


class PlannerAgent:
    def __init__(self):
        self.skills = SkillRegistry()
        self.world = WorldModelService()

    async def run(self, goals: dict[str, Any], constraints: dict[str, Any]) -> list[Hypothesis]:
        """Generate ranked action plans with simulated outcomes."""
        plans = []

        for skill_name in ["simulate_grid_load", "predict_battery_degradation"]:
            skill = self.skills.get(skill_name)
            if skill:
                result = await self.skills.execute(skill_name, goals)
                plans.append(result)

        return plans
