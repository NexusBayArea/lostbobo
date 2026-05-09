from typing import Any

from fastapi import APIRouter

from backend.core.runtime.entity_graph.service import EntityGraphService

router = APIRouter(prefix="/api/v1/core-graph", tags=["core-graph"])


@router.get("/")
async def get_core_graph() -> dict[str, Any]:
    """Live unified WorldState + Entity Graph view."""
    return await EntityGraphService.graph().get_world_state_graph()


@router.get("/snapshot")
async def core_graph_snapshot() -> dict[str, Any]:
    """Lightweight snapshot for dashboard polling."""
    return await EntityGraphService.graph().core_graph_snapshot()
