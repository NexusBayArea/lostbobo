"""SimHPC Agent SDK — Simple interface for swarm agents."""

from __future__ import annotations

import asyncio
from typing import Any

from pydantic import BaseModel

from backend.core.supabase_job_store import SupabaseJobStore
from backend.runtime.swarm.swarm_coordinator import SwarmCoordinator


class AgentParameters(BaseModel):
    """Parameters passed to an agent by the swarm."""

    agent_id: str
    swarm_id: str
    experiment_id: str
    parameters: dict[str, Any]


class AgentResult(BaseModel):
    """Result returned by an agent."""

    metrics: dict[str, float]
    runtime_seconds: float
    metadata: dict[str, Any] = {}


class SimHPCAgent:
    """Simple SDK for swarm agents."""

    def __init__(self):
        self.store = SupabaseJobStore()
        self.coordinator = SwarmCoordinator()

    async def connect(self):
        await self.store.connect()

    async def get_parameters(self) -> AgentParameters:
        """Poll for the next assigned parameters."""
        await self.connect()

        while True:
            jobs = await self.store.dequeue("agent_tasks", limit=1)
            if jobs:
                job = jobs[0]
                return AgentParameters(**job["payload"])
            await asyncio.sleep(0.5)

    async def submit_results(self, result: AgentResult) -> bool:
        """Submit simulation results back to the swarm."""
        await self.connect()

        try:
            await self.store.update_job(
                job_id=result.metadata.get("agent_id"), status="completed", result=result.model_dump()
            )
            return True
        except Exception:
            return False

    async def report_progress(self, progress: float, message: str = ""):
        """Optional: report intermediate progress."""
        await self.store.publish(
            "agent_progress", {"event": "progress_update", "progress": progress, "message": message}
        )


agent = SimHPCAgent()
