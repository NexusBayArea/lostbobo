"""Agent Orchestrator — ties Analyst + Planner into the closed loop."""

from __future__ import annotations

from typing import Any

from backend.core.agents.analyst import AnalystAgent
from backend.core.agents.planner import PlannerAgent


class AgentOrchestrator:
    def __init__(self):
        self.analyst = AnalystAgent()
        self.planner = PlannerAgent()

    async def analyze(self, world_snapshot: dict[str, Any], memory_context: dict[str, Any] | None = None):
        return await self.analyst.run(world_snapshot, memory_context)

    async def plan(self, goals: dict[str, Any], constraints: dict[str, Any]):
        return await self.planner.run(goals, constraints)
