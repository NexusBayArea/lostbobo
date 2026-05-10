from fastapi import APIRouter

from backend.core.runtime.entity_graph.service import EntityGraphService
from backend.core.runtime.provenance.service import ExecutionProvenanceService

router = APIRouter(prefix="/graph", tags=["Visualization"])


@router.get("/provenance/{run_id}")
async def get_provenance_graph(run_id: str, depth: int = 4):
    """Full provenance trace for a specific execution run."""
    return await ExecutionProvenanceService.provenance().get_provenance_trace(run_id, depth)


@router.get("/world-state")
async def get_world_state_graph():
    """Current live WorldState + Entity Graph."""
    return await EntityGraphService.graph().get_world_state_graph()


@router.get("/temporal-snapshot")
async def get_temporal_snapshot(timestamp: str | None = None):
    return await EntityGraphService.graph().get_temporal_snapshot(timestamp)


@router.get("/sla-impact")
async def get_sla_impact_graph():
    return await EntityGraphService.graph().get_sla_impact_view()
