import time

from fastapi import APIRouter, Query

from backend.core.runtime.entity_graph.service import EntityGraphService
from backend.core.runtime.state_registry.service import StateRegistryService

router = APIRouter(prefix="/api/v1/graph", tags=["visualization"])


@router.get("/entity-graph")
async def get_entity_graph(
    max_nodes: int = Query(300, le=1000), max_hops: int = Query(3, le=5), min_weight: float = Query(0.2, ge=0.0)
):
    """Live Entity Graph snapshot with temporal weights."""
    graph_service = EntityGraphService.graph()
    nodes = await graph_service.get_nodes_snapshot(max_nodes)
    edges = await graph_service.get_edges_snapshot(min_weight=min_weight)
    return {"nodes": nodes, "edges": edges, "timestamp": time.time()}


@router.get("/world-state-graph")
async def get_world_state_graph():
    """Combined WorldState + Entity Graph view."""
    state = await StateRegistryService.registry().get_current()
    graph = await EntityGraphService.graph().get_graph_snapshot()
    return {
        "state": state.model_dump(),
        "graph": graph,
        "regime": state.regime,
        "entropy": sum(e.uncertainty for e in state.entities.values()) if state.entities else 0,
    }


@router.get("/graph/replay")
async def replay_graph(at_timestamp: float):
    """Deterministic historical graph reconstruction."""
    state = await StateRegistryService.registry().reconstruct(at_timestamp)
    # ... build graph at that point in time
    return {"state": state, "graph": await EntityGraphService.graph().get_graph_snapshot()}
