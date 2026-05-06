"""Agent API routes — wired through Kernel."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from backend.core.kernel.kernel import Kernel

router = APIRouter(prefix="/agents", tags=["agents"])
kernel = Kernel()


@router.post("/analyst/run")
async def analyst_run(payload: dict[str, Any]) -> dict[str, Any]:
    return await kernel.execute({"type": "AGENT_RUN", "payload": {"agent": "analyst", "input": payload}})


@router.post("/planner/run")
async def planner_run(payload: dict[str, Any]) -> dict[str, Any]:
    return await kernel.execute({"type": "AGENT_RUN", "payload": {"agent": "planner", "input": payload}})
