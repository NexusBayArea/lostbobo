"""World Model API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from backend.core.world_model.schema import WorldState
from backend.core.world_model.service import WorldModelService

router = APIRouter(prefix="/world_model", tags=["world_model"])
service = WorldModelService()


@router.post("/update")
async def update_world(state: dict[str, Any]) -> dict[str, Any]:
    ws = WorldState(**state)
    result = await service.update(ws)
    return {"state_id": result.state_id}


@router.post("/query")
async def query_world(filter: dict[str, Any]) -> list[dict[str, Any]]:
    results = await service.query(filter)
    return [{"state_id": r.state_id, "timestamp": r.timestamp.isoformat()} for r in results]


@router.post("/propagate")
async def propagate(state: dict[str, Any], steps: int = 1000) -> dict[str, Any]:
    ws = WorldState(**state)
    return await service.propagate_uncertainty(ws, steps)
