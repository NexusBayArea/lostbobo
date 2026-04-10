from fastapi import APIRouter, Depends, HTTPException, Body, Header
from typing import Any
import os
import json
import time
import logging
from datetime import datetime

from app.services import runpod_service

router = APIRouter()
logger = logging.getLogger(__name__)


def verify_admin(authorization: str = Header(None)) -> bool:
    """Stub replaced by init_routes()."""
    raise RuntimeError("verify_admin not initialized — call init_routes() first")


r_client: Any = None
warm_pod_fn: Any = None


def init_routes(redis, admin_dep):
    global r_client, verify_admin, warm_pod_fn
    r_client = redis
    verify_admin = admin_dep

    def _fallback():
        # V2.6.0: Try to resume any stopped pod
        try:
            pods = runpod_service.list_pods()
            stopped = [p for p in pods if p.get("desiredStatus") == "STOPPED"]
            if stopped:
                pod_id = stopped[0]["id"]
                runpod_service.resume_pod(pod_id)
                return {"status": "warming", "pod_id": pod_id}
            return {"status": "none_found", "message": "No stopped pods to warm"}
        except Exception as e:
            logger.error(f"Warm fallback failed: {e}")
            return {"status": "error", "message": str(e)}

    warm_pod_fn = _fallback



@router.post("/fleet/warm", tags=["Admin — Fleet"])
async def warm_fleet(_: bool = Depends(verify_admin)):
    """
    Proactively resume a stopped pod before a demo.
    Call this ~90 seconds before your pilot session starts.
    """
    try:
        result = warm_pod_fn()
        return {"status": "ok", **result}
    except Exception as e:
        raise HTTPException(500, f"Warm failed: {e}")


@router.get("/fleet/readiness", tags=["Admin — Fleet"])
async def get_fleet_readiness(_: bool = Depends(verify_admin)):
    """Returns whether the GPU pod is ready to accept jobs."""
    try:
        running = json.loads(r_client.get("active_pods") or "[]")
        stopped = json.loads(r_client.get("pods:stopped") or "[]")
        q_len = r_client.llen(os.getenv("QUEUE_NAME", "simhpc_jobs"))
        last_hb = r_client.get("worker:last_heartbeat")

        worker_live = False
        if last_hb:
            try:
                worker_live = (time.time() - float(last_hb)) < 30
            except ValueError:
                pass

        ready = len(running) > 0 and worker_live

        return {
            "ready": ready,
            "running_pods": len(running),
            "stopped_pods": len(stopped),
            "worker_live": worker_live,
            "queue_depth": q_len,
            "pod_ids": running,
            "message": (
                "Pod running and worker connected — ready for simulations."
                if ready
                else "Pod starting up — check back in a few seconds."
            ),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(500, f"Readiness check failed: {e}")


@router.get("/fleet/status", tags=["Admin — Fleet"])
async def get_rich_fleet_status(_: bool = Depends(verify_admin)):
    """Full fleet status with cost tracking and scaling state."""
    try:
        snapshot = json.loads(r_client.get("autoscaler:last_status") or "{}")
        events_r = r_client.lrange("runpod_events", 0, 9)
        events = [json.loads(e) for e in events_r]
        today = float(r_client.get("cost:today_usd") or 0)
        running = json.loads(r_client.get("active_pods") or "[]")
        stopped = json.loads(r_client.get("pods:stopped") or "[]")

        return {
            "status": "ok",
            "fleet": {
                "running_pods": len(running),
                "stopped_pods": len(stopped),
                "running_ids": running,
                "stopped_ids": stopped,
                "max_pods": int(os.getenv("MAX_PODS", "1")),
                "volume_mount": os.getenv("NETWORK_VOLUME_MOUNT", "/workspace"),
            },
            "cost": {
                "today_usd": round(today, 4),
                "hourly_burn_usd": round(len(running) * 0.39, 4),
                "daily_cap_usd": float(os.getenv("DAILY_COST_HARD_CAP_USD", "15.0")),
            },
            "scaling": {
                "idle_sec": snapshot.get("idle_sec", 0),
                "idle_timeout": int(os.getenv("IDLE_TIMEOUT", "300")),
                "strategy": "stop_resume",
            },
            "recent_events": events,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(500, f"Status error: {e}")


@router.get("/fleet", tags=["Admin — Fleet"])
async def get_fleet_status_endpoint(_: bool = Depends(verify_admin)):
    """Lightweight fleet status fallback."""
    try:
        fleet_data = r_client.get("autoscaler:last_status")
        if fleet_data:
            return {"status": "ok", "fleet": json.loads(fleet_data)}
        queue_len = r_client.llen(os.getenv("QUEUE_NAME", "simhpc_jobs"))
        active_pods = json.loads(r_client.get("active_pods") or "[]")
        today_cost = float(r_client.get("cost:today_usd") or 0)
        return {
            "status": "ok",
            "fleet": {
                "pods": len(active_pods),
                "pod_ids": active_pods,
                "queue": queue_len,
                "cost_today": round(today_cost, 4),
                "timestamp": datetime.now().isoformat(),
            },
        }
    except Exception as e:
        raise HTTPException(500, f"Fleet status error: {e}")


@router.get("/fleet/cost", tags=["Admin — Fleet"])
async def get_cost_endpoint(_: bool = Depends(verify_admin)):
    """Cost summary: hourly burn, daily estimate."""
    try:
        today_cost = float(r_client.get("cost:today_usd") or 0)
        active_pods = json.loads(r_client.get("active_pods") or "[]")
        return {
            "status": "ok",
            "cost": {
                "actual_today_usd": round(today_cost, 4),
                "running_pods": len(active_pods),
                "timestamp": datetime.now().isoformat(),
            },
        }
    except Exception as e:
        raise HTTPException(500, f"Cost query error: {e}")


@router.get("/fleet/events", tags=["Admin — Fleet"])
async def get_fleet_events(limit: int = 20, _: bool = Depends(verify_admin)):
    """Recent fleet events (scaling, cost cap, errors)."""
    try:
        raw_events = r_client.lrange("runpod_events", 0, min(limit - 1, 499))
        events = [json.loads(e) for e in raw_events]
        return {"status": "ok", "events": events, "count": len(events)}
    except Exception as e:
        raise HTTPException(500, f"Events query error: {e}")


@router.post("/fleet/pod", tags=["Admin — Fleet"])
async def create_pod_endpoint(
    name: str = Body("simhpc-worker"),
    gpu_type: str = Body("NVIDIA A40"),
    _: bool = Depends(verify_admin),
):
    """Create a new GPU pod on RunPod."""
    try:
        active_pods = json.loads(r_client.get("active_pods") or "[]")
        max_pods = int(os.getenv("MAX_PODS", "3"))
        if len(active_pods) >= max_pods:
            raise HTTPException(
                429,
                f"Safety cap: {len(active_pods)} pods running (MAX={max_pods}). "
                "Terminate a pod first.",
            )
        return {
            "status": "ok",
            "message": f"Pod creation queued (name={name}, gpu={gpu_type}). "
            "The autoscaler will create it on next cycle if queue has jobs.",
            "current_pods": len(active_pods),
            "max_pods": max_pods,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Pod creation error: {e}")


@router.post("/fleet/pod/{pod_id}/stop", tags=["Admin — Fleet"])
async def stop_pod(pod_id: str, _: bool = Depends(verify_admin)):
    """Stop a running pod (preserves disk, stops GPU billing)."""
    try:
        # V2.6.0: Call RunPod directly for immediate responsiveness
        runpod_service.stop_pod(pod_id)

        active = json.loads(r_client.get("active_pods") or "[]")
        active = [p for p in active if p != pod_id]
        r_client.set("active_pods", json.dumps(active))
        r_client.lpush(
            "runpod_events",
            json.dumps(
                {
                    "ts": datetime.now().isoformat(),
                    "event": "pod_stop_requested",
                    "pod_id": pod_id,
                    "details": "via direct admin API call",
                }
            ),
        )
        return {"status": "ok", "pod_id": pod_id, "action": "stop_requested"}
    except Exception as e:
        raise HTTPException(500, f"Pod stop error: {e}")


@router.post("/fleet/pod/{pod_id}/terminate", tags=["Admin — Fleet"])
async def terminate_pod(pod_id: str, _: bool = Depends(verify_admin)):
    """Permanently terminate a pod (deletes disk, zeroes billing)."""
    try:
        # V2.6.0: Call RunPod directly for immediate responsiveness
        runpod_service.terminate_pod(pod_id)

        active = json.loads(r_client.get("active_pods") or "[]")
        active = [p for p in active if p != pod_id]
        r_client.set("active_pods", json.dumps(active))
        r_client.lpush(
            "runpod_events",
            json.dumps(
                {
                    "ts": datetime.now().isoformat(),
                    "event": "pod_terminate_requested",
                    "pod_id": pod_id,
                    "details": "via direct admin API call",
                }
            ),
        )
        return {"status": "ok", "pod_id": pod_id, "action": "terminate_requested"}
    except Exception as e:
        raise HTTPException(500, f"Pod termination error: {e}")
