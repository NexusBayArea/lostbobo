"""Agent API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from backend.core.agents.orchestrator import AgentOrchestrator

router = APIRouter(prefix="/agents", tags=["agents"])
orchestrator = AgentOrchestrator()


@router.post("/analyst/run")
async def analyst_run(payload: dict[str, Any]) -> dict[str, Any]:
    results = await orchestrator.analyze(payload.get("world_snapshot", {}), payload.get("memory_context"))
    return {"hypotheses": [{"id": h.id} for h in results]}


@router.post("/planner/run")
async def planner_run(payload: dict[str, Any]) -> dict[str, Any]:
    results = await orchestrator.plan(payload.get("goals", {}), payload.get("constraints", {}))
    return {"plans": [{"id": h.id} for h in results]}
