"""
SimHPC RunPod API Client — Production Pod Lifecycle Management

Provides a unified interface for:
  - Creating / starting / stopping / terminating pods
  - Listing pod fleet status
  - Cost estimation & tracking
  - Health monitoring & diagnostics

Uses RunPod GraphQL API (not REST, not serverless).
All state is persisted in Redis for crash recovery.
"""

import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import redis
import requests

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Pod creation defaults (override via env)
DEFAULT_GPU_TYPE = os.getenv("RUNPOD_GPU_TYPE", "NVIDIA A40")
DEFAULT_IMAGE = os.getenv("RUNPOD_WORKER_IMAGE", "simhpcworker/simhpc-worker:latest")
DEFAULT_CLOUD_TYPE = os.getenv("RUNPOD_CLOUD_TYPE", "SECURE")
DEFAULT_CONTAINER_DISK_GB = int(os.getenv("RUNPOD_CONTAINER_DISK_GB", "20"))
DEFAULT_VOLUME_GB = int(os.getenv("RUNPOD_VOLUME_GB", "0"))

# Safety
MAX_PODS = int(os.getenv("MAX_PODS", "3"))
JOBS_PER_POD = int(os.getenv("JOBS_PER_POD", "2"))
IDLE_TIMEOUT = int(os.getenv("IDLE_TIMEOUT", "300"))  # 5 min
SCALE_UP_COOLDOWN = int(os.getenv("SCALE_UP_COOLDOWN", "30"))

# Cost estimates ($/hr) — conservative for alpha budgeting
GPU_COST_PER_HOUR = {
    "NVIDIA A40": 0.39,
    "NVIDIA RTX 3090": 0.22,
    "NVIDIA RTX A5000": 0.32,
    "NVIDIA A100 80GB": 1.64,
}

logger = logging.getLogger("runpod_api")
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

redis_client = redis.from_url(REDIS_URL, decode_responses=True)

RUNPOD_GQL_URL = f"https://api.runpod.io/graphql?api_key={RUNPOD_API_KEY}"


# ---------------------------------------------------------------------------
# DATA MODELS
# ---------------------------------------------------------------------------
@dataclass
class PodInfo:
    pod_id: str
    name: str
    status: str  # RUNNING, STOPPED, EXITED, etc.
    gpu_type: str
    image: str
    uptime_sec: float
    cost_estimate_usd: float
    created_at: str


# ---------------------------------------------------------------------------
# LOW-LEVEL GRAPHQL
# ---------------------------------------------------------------------------
def _gql(query: str) -> dict:
    """Execute a RunPod GraphQL query."""
    if not RUNPOD_API_KEY:
        raise RuntimeError("RUNPOD_API_KEY not set")
    resp = requests.post(RUNPOD_GQL_URL, json={"query": query}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"RunPod GraphQL error: {data['errors']}")
    return data


# ---------------------------------------------------------------------------
# POD STATE (REDIS PERSISTENCE)
# ---------------------------------------------------------------------------
def _load_pods() -> list:
    raw = redis_client.get("active_pods")
    return json.loads(raw) if raw else []


def _save_pods(pods: list):
    redis_client.set("active_pods", json.dumps(pods))


def _record_event(event_type: str, pod_id: str = "", details: str = ""):
    """Append to a capped Redis list for audit trail."""
    entry = json.dumps(
        {
            "ts": datetime.utcnow().isoformat(),
            "event": event_type,
            "pod_id": pod_id,
            "details": details,
        }
    )
    redis_client.lpush("runpod_events", entry)
    redis_client.ltrim("runpod_events", 0, 499)  # keep last 500


def _update_cost_tracking(pod_count: int, interval_sec: int, gpu_type: str = DEFAULT_GPU_TYPE):
    """Accumulate estimated cost in Redis based on actual polling interval."""
    hourly = GPU_COST_PER_HOUR.get(gpu_type, 0.39)
    # Pro-rate based on the actual interval passed from the autoscaler
    cost_delta = (hourly / 3600) * interval_sec * pod_count
    redis_client.incrbyfloat("cost:today_usd", cost_delta)
    # Reset daily counter at midnight (86400 seconds)
    redis_client.expire("cost:today_usd", 86400)



# ---------------------------------------------------------------------------
# PUBLIC API — POD LIFECYCLE
# ---------------------------------------------------------------------------
def list_pods() -> list[dict]:
    """
    Fetch all pods from RunPod API, sync with Redis state.
    Returns list of pod dicts with status + cost estimate.
    """
    query = """
    query {
      myself {
        pods {
          id
          name
          desiredStatus
          runtime {
            uptimeInSeconds
            gpus { id gpuUtilPercent memoryUtilPercent }
          }
          imageName
          gpuDisplayName
          costPerHr
          machine { gpuDisplayName }
        }
      }
    }
    """
    res = _gql(query)
    pods = res["data"]["myself"]["pods"]

    result = []
    running_ids = []
    for p in pods:
        runtime = p.get("runtime") or {}
        uptime = runtime.get("uptimeInSeconds", 0) or 0
        cost_hr = p.get("costPerHr", 0) or 0
        cost_est = (uptime / 3600) * cost_hr

        info = {
            "pod_id": p["id"],
            "name": p.get("name", "unknown"),
            "status": p.get("desiredStatus", "UNKNOWN"),
            "gpu_type": p.get("gpuDisplayName")
            or (p.get("machine") or {}).get("gpuDisplayName", "N/A"),
            "image": p.get("imageName", "unknown"),
            "uptime_sec": uptime,
            "cost_estimate_usd": round(cost_est, 4),
            "cost_per_hr": cost_hr,
            "gpus": runtime.get("gpus", []),
        }
        result.append(info)
        if p.get("desiredStatus") == "RUNNING":
            running_ids.append(p["id"])

    # Sync Redis with reality
    _save_pods(running_ids)
    return result


def get_pod(pod_id: str) -> Optional[dict]:
    """Get details of a specific pod."""
    pods = list_pods()
    for p in pods:
        if p["pod_id"] == pod_id:
            return p
    return None


def create_pod(
    name: str = "simhpc-worker",
    gpu_type: str = DEFAULT_GPU_TYPE,
    image: str = DEFAULT_IMAGE,
    cloud_type: str = DEFAULT_CLOUD_TYPE,
    container_disk_gb: int = DEFAULT_CONTAINER_DISK_GB,
    volume_gb: int = DEFAULT_VOLUME_GB,
    env_vars: list[dict] = None,
) -> dict:
    """
    Create and deploy a new GPU pod on RunPod.
    Respects MAX_PODS safety cap.
    Returns pod info dict with id.
    """
    active = _load_pods()
    if len(active) >= MAX_PODS:
        raise RuntimeError(
            f"Safety cap: {len(active)} pods running (MAX_PODS={MAX_PODS}). "
            "Terminate an existing pod first."
        )

    # Build env string for GraphQL mutation
    env_str = ""
    if env_vars:
        env_entries = ", ".join(
            f'{{ key: "{e["key"]}", value: "{e["value"]}" }}' for e in env_vars
        )
        env_str = f", env: [{env_entries}]"

    query = f"""
    mutation {{
      podFindAndDeployOnDemand(input: {{
        name: "{name}",
        imageName: "{image}",
        gpuTypeId: "{gpu_type}",
        cloudType: {cloud_type},
        containerDiskInGb: {container_disk_gb},
        volumeInGb: {volume_gb}{env_str}
      }}) {{
        id
        desiredStatus
        imageName
        machine {{ gpuDisplayName }}
        costPerHr
      }}
    }}
    """

    res = _gql(query)
    pod_data = res["data"]["podFindAndDeployOnDemand"]
    pod_id = pod_data["id"]

    active.append(pod_id)
    _save_pods(active)
    _record_event("pod_created", pod_id, f"gpu={gpu_type}, image={image}")

    logger.info(f"Pod created: {pod_id} ({len(active)}/{MAX_PODS})")

    return {
        "pod_id": pod_id,
        "status": pod_data.get("desiredStatus", "RUNNING"),
        "image": pod_data.get("imageName"),
        "gpu_type": (pod_data.get("machine") or {}).get("gpuDisplayName", gpu_type),
        "cost_per_hr": pod_data.get("costPerHr", 0),
    }


def start_pod(pod_id: str) -> dict:
    """Resume a stopped pod (without re-creating it)."""
    query = f"""
    mutation {{
      podResume(input: {{ podId: "{pod_id}", gpuCount: 1 }}) {{
        id
        desiredStatus
        costPerHr
      }}
    }}
    """
    res = _gql(query)
    pod_data = res["data"]["podResume"]

    active = _load_pods()
    if pod_id not in active:
        active.append(pod_id)
        _save_pods(active)

    _record_event("pod_started", pod_id)
    logger.info(f"Pod started: {pod_id}")

    return {
        "pod_id": pod_data["id"],
        "status": pod_data.get("desiredStatus", "RUNNING"),
        "cost_per_hr": pod_data.get("costPerHr", 0),
    }


def stop_pod(pod_id: str) -> dict:
    """
    Stop a pod (preserves disk, stops billing for GPU).
    Use this for cost control — pod can be resumed later.
    """
    query = f"""
    mutation {{
      podStop(input: {{ podId: "{pod_id}" }}) {{
        id
        desiredStatus
      }}
    }}
    """
    res = _gql(query)
    pod_data = res["data"]["podStop"]

    active = _load_pods()
    active = [p for p in active if p != pod_id]
    _save_pods(active)

    _record_event("pod_stopped", pod_id)
    logger.info(f"Pod stopped: {pod_id}")

    return {
        "pod_id": pod_data["id"],
        "status": pod_data.get("desiredStatus", "STOPPED"),
    }


def terminate_pod(pod_id: str) -> dict:
    """
    Permanently destroy a pod (deletes disk, zeroes billing).
    Use for idle shutdown or scale-down.
    """
    query = f"""
    mutation {{
      podTerminate(input: {{ podId: "{pod_id}" }})
    }}
    """
    _gql(query)

    active = _load_pods()
    active = [p for p in active if p != pod_id]
    _save_pods(active)

    _record_event("pod_terminated", pod_id)
    logger.info(f"Pod terminated: {pod_id}")

    return {"pod_id": pod_id, "status": "TERMINATED"}


# ---------------------------------------------------------------------------
# PUBLIC API — FLEET MANAGEMENT
# ---------------------------------------------------------------------------
def get_fleet_status() -> dict:
    """
    Comprehensive fleet status for the admin dashboard.
    Includes running pods, queue depth, cost tracking, and scaling state.
    """
    pods = list_pods()
    running = [p for p in pods if p["status"] == "RUNNING"]
    stopped = [p for p in pods if p["status"] == "STOPPED"]

    # Queue depth
    queue_name = os.getenv("QUEUE_NAME", "simhpc_jobs")
    queue_len = redis_client.llen(queue_name)

    # Cost tracking
    today_cost = float(redis_client.get("cost:today_usd") or 0)

    # Last active time
    last_active_raw = redis_client.get("last_active_time")
    last_active = float(last_active_raw) if last_active_raw else time.time()
    idle_sec = time.time() - last_active if queue_len == 0 else 0

    # Recent events (last 20)
    raw_events = redis_client.lrange("runpod_events", 0, 19)
    events = [json.loads(e) for e in raw_events]

    return {
        "fleet": {
            "running_pods": len(running),
            "stopped_pods": len(stopped),
            "total_pods": len(pods),
            "max_pods": MAX_PODS,
            "pods": pods,
        },
        "queue": {
            "depth": queue_len,
            "jobs_per_pod": JOBS_PER_POD,
            "capacity": len(running) * JOBS_PER_POD,
        },
        "cost": {
            "today_usd": round(today_cost, 4),
            "hourly_burn_usd": round(sum(p.get("cost_per_hr", 0) for p in running), 4),
            "idle_shutdown_sec": IDLE_TIMEOUT,
        },
        "scaling": {
            "idle_sec": round(idle_sec, 1),
            "idle_timeout": IDLE_TIMEOUT,
            "scale_up_cooldown": SCALE_UP_COOLDOWN,
            "will_shutdown_in": max(0, round(IDLE_TIMEOUT - idle_sec, 1))
            if idle_sec > 0
            else None,
        },
        "recent_events": events,
        "timestamp": datetime.utcnow().isoformat(),
    }


def get_cost_summary() -> dict:
    """
    Cost summary with estimates for daily/weekly burn.
    """
    pods = list_pods()
    running = [p for p in pods if p["status"] == "RUNNING"]
    hourly = sum(p.get("cost_per_hr", 0) for p in running)
    today = float(redis_client.get("cost:today_usd") or 0)

    return {
        "current_hourly_burn_usd": round(hourly, 4),
        "estimated_daily_usd": round(hourly * 24, 2),
        "estimated_weekly_usd": round(hourly * 24 * 7, 2),
        "actual_today_usd": round(today, 4),
        "running_pods": len(running),
        "cost_without_autoscaler_daily": round(hourly * 24, 2),  # if left running 24/7
        "cost_with_autoscaler_daily": round(today, 4),  # actual (autoscaler stops idle)
        "savings_percent": round((1 - (today / max(hourly * 24, 0.01))) * 100, 1)
        if hourly > 0
        else 100.0,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------------------------
def health_check() -> dict:
    """Quick health check — verifies RunPod API key and connectivity."""
    try:
        query = """
        query {
          myself {
            id
            currentSpendPerHr
            machineQuota
          }
        }
        """
        res = _gql(query)
        myself = res["data"]["myself"]
        return {
            "status": "healthy",
            "account_id": myself.get("id"),
            "current_spend_per_hr": myself.get("currentSpendPerHr"),
            "machine_quota": myself.get("machineQuota"),
            "api_key_valid": True,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "api_key_valid": False,
            "timestamp": datetime.utcnow().isoformat(),
        }
