import os
import time
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

# Load environment variables from .env file
load_dotenv()

import redis
from runpod_api import (
    list_pods,
    create_pod,
    stop_pod,
    terminate_pod,
    get_fleet_status,
    get_cost_summary,
    health_check,
    _load_pods,
    _save_pods,
    _record_event,
    _update_cost_tracking,
    MAX_PODS,
    JOBS_PER_POD,
    IDLE_TIMEOUT,
    SCALE_UP_COOLDOWN,
    DEFAULT_GPU_TYPE,
)

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_NAME = os.getenv("QUEUE_NAME", "simhpc_jobs")
INFLIGHT_KEY = os.getenv("INFLIGHT_KEY", "simhpc_inflight")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "10"))

# Cost alerting thresholds
DAILY_COST_WARN_USD = float(os.getenv("DAILY_COST_WARN_USD", "10.0"))
DAILY_COST_HARD_CAP_USD = float(os.getenv("DAILY_COST_HARD_CAP_USD", "25.0"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [AUTOSCALER] %(levelname)s - %(message)s",
)
logger = logging.getLogger("autoscaler")

redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# ---------------------------------------------------------------------------
# STATE
# ---------------------------------------------------------------------------
last_scale_time = 0
last_active_time = time.time()
last_status_log = 0
STATUS_LOG_INTERVAL = 60  # log full status every 60s

# ---------------------------------------------------------------------------
# RETRY-PROTECTED API CALLS
# ---------------------------------------------------------------------------
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def list_pods_with_retry():
    return list_pods()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def create_pod_with_retry():
    return create_pod()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def terminate_pod_with_retry(pod_id):
    return terminate_pod(pod_id)

# ---------------------------------------------------------------------------
# SYNC WITH RUNPOD API
# ---------------------------------------------------------------------------
def sync_pods() -> list:
    """
    Query RunPod API for live pod list, reconcile with Redis state.
    Returns list of running pod IDs.
    """
    try:
        all_pods = list_pods_with_retry()
        running_ids = [p["pod_id"] for p in all_pods if p["status"] == "RUNNING"]

        stored = set(_load_pods())
        live = set(running_ids)

        # Detect drift
        dead = stored - live
        if dead:
            logger.warning(f"Synced out dead pods: {dead}")
            _record_event("sync_dead", details=f"removed: {list(dead)}")

        orphaned = live - stored
        if orphaned:
            logger.info(f"Synced in orphaned pods: {orphaned}")
            _record_event("sync_orphaned", details=f"added: {list(orphaned)}")

        _save_pods(list(live))
        return list(live)

    except Exception as e:
        logger.error(f"Failed to sync pods: {e}")
        return _load_pods()

# ---------------------------------------------------------------------------
# SCALING LOGIC
# ---------------------------------------------------------------------------
def scale():
    global last_scale_time, last_active_time, last_status_log

    q_len = redis_client.llen(QUEUE_NAME)
    inflight = int(redis_client.get(INFLIGHT_KEY) or 0)
    total_work = q_len + inflight
    
    active_pod_ids = sync_pods()
    current = len(active_pod_ids)

    # Track cost
    _update_cost_tracking(current, DEFAULT_GPU_TYPE)

    now = time.time()
    if now - last_status_log > STATUS_LOG_INTERVAL:
        cost = get_cost_summary()
        logger.info(f"Fleet: {current}/{MAX_PODS} pods | Work: {total_work} (Q:{q_len}, INF:{inflight}) | Today: ${cost['actual_today_usd']:.3f}")
        last_status_log = now

    # SCALE UP
    if total_work > 0:
        last_active_time = now
        redis_client.set("last_active_time", str(now))

        needed = min(MAX_PODS, (total_work + JOBS_PER_POD - 1) // JOBS_PER_POD)

        if needed > current and (now - last_scale_time) > SCALE_UP_COOLDOWN:
            today_cost = float(redis_client.get("cost:today_usd") or 0)
            if today_cost >= DAILY_COST_HARD_CAP_USD:
                logger.warning(f"Scale-up blocked by cost cap: ${today_cost:.2f}")
                return

            try:
                logger.info(f"Scaling up: {current} -> {current + 1}")
                res = create_pod_with_retry()
                last_scale_time = now
                _record_event("scale_up", res["pod_id"], f"work={total_work}")
            except Exception as e:
                logger.error(f"Scale up failed: {e}")

    # SCALE DOWN
    elif total_work == 0 and current > 0:
        idle_time = now - last_active_time
        if idle_time > IDLE_TIMEOUT:
            logger.info(f"Idle {idle_time:.0f}s > {IDLE_TIMEOUT}s. Shutting down {current} pods.")
            for pod_id in active_pod_ids:
                try:
                    terminate_pod_with_retry(pod_id)
                except Exception as e:
                    logger.error(f"Failed to terminate {pod_id}: {e}")

def run():
    logger.info(f"SimHPC Production Autoscaler v2.2.1 (GraphQL + Tenacity)")
    while True:
        try:
            scale()
        except Exception as e:
            logger.error(f"Main loop error: {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run()
