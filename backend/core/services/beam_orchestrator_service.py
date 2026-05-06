"""BeamOrchestratorService — FastAPI service exposing the full orchestrator."""

from __future__ import annotations

import time

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from backend.core.agents.orchestrator import AgentOrchestrator
from backend.core.orchestrator.beam_orchestrator import BeamOrchestrator
from backend.core.redis.beam_streamer import BeamStreamer
from backend.core.skills.registry import SkillRegistry
from backend.runtime.rag.router import RAGRouter

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


class BeamRequest(BaseModel):
    query: str
    tenant_id: str = "public"
    beam_width: int = 5
    exit_threshold: float = 0.88


class BeamOrchestratorService:
    def __init__(self):
        self.agents = AgentOrchestrator()
        self.skills = SkillRegistry()
        self.streamer = BeamStreamer()
        self.orchestrator = BeamOrchestrator(
            agents=[],
            rag=RAGRouter(),
            config={
                "beam_width": 5,
                "exit_threshold": 0.88,
                "stages": ["plausibility", "rag", "simulation", "robustness"],
            },
        )

    async def run_beam(self, request: BeamRequest, background_tasks: BackgroundTasks):
        result = await self.orchestrator.run(request.query, request.tenant_id)
        return {
            "request_id": f"req_{int(time.time()*1000)}",
            "hypothesis_id": result.id,
            "trust_score": result.trust_score,
            "stage": result.stage,
            "certificate_id": getattr(result, "certificate_id", None),
        }


service = BeamOrchestratorService()


@router.post("/run")
async def run_orchestrator(request: BeamRequest, background_tasks: BackgroundTasks):
    return await service.run_beam(request, background_tasks)
