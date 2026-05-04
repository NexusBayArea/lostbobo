from fastapi import APIRouter

from backend.runtime.dag_executor import execute_dag
from backend.runtime.execution_intelligence import INTELLIGENCE
from backend.runtime.graph import GRAPH
from backend.runtime.manifest import load_manifest

router = APIRouter(prefix="/dag", tags=["DAG"])


@router.get("/graph")
async def get_dag_graph():
    """Return current DAG structure for frontend."""
    manifest = load_manifest()
    nodes = []

    for node_id, node in GRAPH.nodes.items():
        nodes.append(
            {
                "id": node_id,
                "type": node.metadata.get("type", "default"),
                "data": {
                    "label": node_id,
                    "status": "idle",
                    "gpu": node.metadata.get("gpu", False),
                },
                "position": {"x": 0, "y": 0},
                "deps": node.deps,
            }
        )

    return {
        "nodes": nodes,
        "edges": [
            {"id": f"e-{dep}-{nid}", "source": dep, "target": nid}
            for nid, node in GRAPH.nodes.items()
            for dep in node.deps
        ],
        "manifest": manifest,
    }


@router.post("/run")
async def run_dag():
    """Trigger full DAG execution."""
    trace = await execute_dag()
    return {"status": "running", "trace_id": trace.timestamp}


@router.get("/intelligence")
async def get_intelligence():
    """Get analysis, optimizer suggestions, etc."""
    return INTELLIGENCE.full_analysis()
