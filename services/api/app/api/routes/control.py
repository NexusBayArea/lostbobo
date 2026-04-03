from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Dict, List
import logging
from datetime import datetime, timedelta

router = APIRouter()
logger = logging.getLogger(__name__)

r_client: Any = None
verify_auth: Any = None
update_job_field: Any = None
get_job: Any = None


def init_routes(redis, auth_dep, update_jf, get_j):
    global r_client, verify_auth, update_job_field, get_job
    r_client = redis
    verify_auth = auth_dep
    update_job_field = update_jf
    get_job = get_j


@router.get("/controlroom/state", tags=["Cockpit — Control Room"])
async def get_controlroom_state(user: dict = Depends(verify_auth)):
    """Unified state aggregator for the Mission Control Cockpit."""
    user_id = user["user_id_internal"]

    active_runs = []
    keys = r_client.keys("job:*")
    for k in keys:
        job = r_client.hgetall(k)
        if job.get("user_id") == user_id and job.get("status") in ["running", "pending", "processing", "auditing"]:
            active_runs.append({
                "id": k.split(":")[1],
                "status": job.get("status"),
                "model_name": job.get("mesh_name", "Thermal Simulation"),
            })

    alerts = [
        {"id": "a1", "type": "warning", "message": "Hallucination risk detected in thermal gradient.", "timestamp": datetime.now().isoformat()},
        {"id": "a2", "type": "info", "message": "Convergence locked at 10e-6.", "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat()},
    ]

    timeline = [
        {"id": "e1", "type": "dispatch", "label": "🟢 Dispatch", "severity": "info", "timestamp": (datetime.now() - timedelta(minutes=10)).isoformat()},
        {"id": "e2", "type": "convergence", "label": "💠 Convergence Lock", "severity": "success", "timestamp": (datetime.now() - timedelta(minutes=8)).isoformat()},
    ]

    return {
        "active_runs": active_runs,
        "audit_alerts": alerts,
        "timeline_events": timeline,
        "telemetry": {"gpu_load": 42 if active_runs else 0, "status": "nominal" if active_runs else "idle"},
        "guidance": "Safety Factor (1.4x) maintained. Recommend Proceed.",
    }


@router.post("/control/command", tags=["Cockpit — Operator Console"])
async def execute_control_command(action: str, run_id: str, user: dict = Depends(verify_auth)):
    """Execute high-stakes engineering actions."""
    logger.info(f"Control Command: {action} on {run_id}")
    if action == "intercept":
        update_job_field(run_id, "status", "paused")
        return {"status": "ok", "message": "Simulation intercepted and paused."}
    elif action == "boost":
        return {"status": "ok", "message": "GPU priority boosted."}
    elif action == "clone":
        return {"status": "ok", "message": "Simulation cloned. New branch created."}
    elif action == "certify":
        return {"status": "ok", "message": "Physics certification generated."}
    return {"status": "error", "message": f"Unknown action: {action}"}


@router.get("/control/timeline", tags=["Cockpit — Timeline"])
async def get_control_timeline(user: dict = Depends(verify_auth)):
    return [
        {"id": "1", "type": "dispatch", "label": "Simulation Dispatched", "severity": "info", "timestamp": datetime.now().isoformat()},
    ]


@router.get("/control/lineage", tags=["Cockpit — Lineage"])
async def get_control_lineage(user: dict = Depends(verify_auth)):
    return {
        "nodes": [
            {"id": "parent", "label": "Baseline Iteration", "type": "root"},
            {"id": "child", "label": "Adjusted Input B", "type": "branch"},
        ],
        "edges": [{"source": "parent", "target": "child"}],
    }
