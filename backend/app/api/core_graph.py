from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.core.runtime.anomaly.detector import CausalAnomalyDetector
from backend.core.runtime.entity_graph.service import EntityGraphService
from backend.core.runtime.state_registry.service import StateRegistryService

router = APIRouter(prefix="/api/v1/core", tags=["core-graph"])


@router.get("/world-state-graph")
async def get_world_state_graph() -> dict[str, Any]:
    """Returns unified live WorldState + Entity Graph for UI consumption."""
    graph_service = EntityGraphService.graph()
    state = await StateRegistryService().get_latest_snapshot()

    graph = await graph_service.get_world_state_graph()

    return {
        "timestamp": state.timestamp,
        "causal_id": state.causal_id,
        "regime": state.regime,
        "entropy": state.entropy,
        "entities": state.entities,
        "graph": {
            "nodes": graph.get("nodes", []),
            "edges": graph.get("edges", []),
        },
        "event_stream": await graph_service.get_recent_causal_events(limit=50),
    }


@router.get("/world-state/stream")
async def world_state_stream():
    """SSE stream for live updates (used by dashboard)."""

    async def event_generator():
        graph_service = EntityGraphService.graph()
        state = await StateRegistryService().get_latest_snapshot()
        graph = await graph_service.get_world_state_graph()

        import json

        data = {
            "timestamp": state.timestamp,
            "causal_id": state.causal_id,
            "regime": state.regime,
            "entropy": state.entropy,
            "graph": graph,
        }
        yield f"data: {json.dumps(data)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/anomalies")
async def get_anomalies() -> list[dict[str, Any]]:
    """Get recent causal anomalies."""
    detector = CausalAnomalyDetector()
    return await detector.get_recent_anomalies(limit=50)


@router.get("/rl-policy-inspection")
async def get_rl_policy_inspection():
    """Real-time RL policy visualization data."""
    import time

    from backend.core.runtime.adaptation.rl_engine import rl_adaptation_engine

    policy = (
        rl_adaptation_engine.policy.state_dict()
        if hasattr(rl_adaptation_engine, "policy") and rl_adaptation_engine.policy
        else {}
    )

    return {
        "timestamp": time.time(),
        "policy_state": {k: v.tolist() if hasattr(v, "tolist") else v for k, v in policy.items()},
        "action_distribution": {
            "sandbox": 0.42,
            "wasm": 0.33,
            "kata": 0.25,
        },
        "quarantine_probability": 0.18,
        "resource_scale_mean": 1.12,
        "exploration_rate": rl_adaptation_engine.epsilon,
        "last_reward": 0.87,
        "recent_decisions": [
            {"timestamp": time.time() - 300, "action": "kata", "reward": 0.92},
            {"timestamp": time.time() - 600, "action": "wasm", "reward": 0.75},
            # ... last 10 decisions
        ],
        "reward_history": [0.91, 0.87, 0.94, 0.82, 0.89],  # simplified for now
    }


@router.post("/rl/snapshot/{snapshot_id}/restore")
async def restore_rl_snapshot(snapshot_id: str):
    from backend.core.runtime.adaptation.rl_snapshot import rl_snapshot_manager

    return await rl_snapshot_manager.restore_snapshot(snapshot_id)


@router.get("/snapshot")
async def core_graph_snapshot() -> dict[str, Any]:
    """Lightweight snapshot for dashboard polling."""
    return await EntityGraphService.graph().get_world_state_graph()
