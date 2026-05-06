"""BeamOrchestrator API — wired through Kernel."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from backend.core.kernel.kernel import Kernel

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])
kernel = Kernel()


class BeamRequest(BaseModel):
    query: str
    tenant_id: str = "public"


@router.post("/run")
async def run_beam(request: BeamRequest, background_tasks: BackgroundTasks) -> dict[str, Any]:
    return await kernel.execute(
        {
            "type": "AGENT_RUN",
            "payload": {"agent": "planner", "input": {"query": request.query, "tenant_id": request.tenant_id}},
        }
    )
