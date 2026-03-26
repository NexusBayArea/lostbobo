"""
SimHPC Production Autoscaler (v2.2.0)

Queue-aware + Cost-aware + GPU-aware autoscaler for RunPod Pods.

Features:
  - Polls Redis queue depth every CHECK_INTERVAL seconds
  - Scales up: ceil(queue / JOBS_PER_POD) new pods, one at a time, with cooldown
  - Scales down: terminates ALL pods after IDLE_TIMEOUT idle
  - Cost tracking: accumulates per-interval cost estimates in Redis
  - Fleet sync: reconciles Redis-persisted pod list against RunPod API each cycle
  - Monitoring: logs fleet status, cost, and scaling decisions to Redis event log
  - Safety: MAX_PODS hard cap enforced in code AND against API

Uses RunPod GraphQL API — NOT REST, NOT serverless.
"""

import os
import sys
import json
import time
import logging
from datetime import datetime

# Add parent directory to path so we can import runpod_api
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

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
# SYNC WITH RUNPOD API (via runpod_api module)
# ---------------------------------------------------------------------------
def sync_pods() -> list:
    """
    Query RunPod API for live pod list, reconcile with Redis state.
    Returns list of running pod IDs.
    """
    try:
        all_pods = list_pods()
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
        # Fall back to cached state
        return _load_pods()


# ---------------------------------------------------------------------------
# COST GUARD
# ---------------------------------------------------------------------------
def check_cost_guard() -> bool:
    """
    Returns True if we're within budget. False if daily cap exceeded.
    """
    today_cost = float(redis_client.get("cost:today_usd") or 0)

    if today_cost >= DAILY_COST_HARD_CAP_USD:
        logger.critical(
            f"COST HARD CAP REACHED: ${today_cost:.2f} >= ${DAILY_COST_HARD_CAP_USD:.2f}. "
            "Blocking scale-up."
        )
        _record_event("cost_cap_reached", details=f"${today_cost:.2f}")
        return False

    if today_cost >= DAILY_COST_WARN_USD:
        logger.warning(
            f"COST WARNING: ${today_cost:.2f} approaching cap ${DAILY_COST_HARD_CAP_USD:.2f}"
        )

    return True


# ---------------------------------------------------------------------------
# SCALING LOGIC
# ---------------------------------------------------------------------------
def scale():
    """
    Main scaling decision loop.
    Called every CHECK_INTERVAL seconds.
    """
    global last_scale_time, last_active_time, last_status_log

    q_len = redis_client.llen(QUEUE_NAME)
    active_pods = sync_pods()
    current = len(active_pods)

    # Track cost
    _update_cost_tracking(current, DEFAULT_GPU_TYPE)

    # Periodic status logging
    now = time.time()
    if now - last_status_log > STATUS_LOG_INTERVAL:
        cost = get_cost_summary()
        logger.info(
            f"Fleet: {current}/{MAX_PODS} pods | Queue: {q_len} | "
            f"Hourly: ${cost['current_hourly_burn_usd']:.3f} | "
            f"Today: ${cost['actual_today_usd']:.3f}"
        )
        # Store fleet snapshot for dashboard
        redis_client.set("autoscaler:last_status", json.dumps({
            "pods": current,
            "max_pods": MAX_PODS,
            "queue": q_len,
            "cost_hourly": cost["current_hourly_burn_usd"],
            "cost_today": cost["actual_today_usd"],
            "idle_sec": round(now - last_active_time, 1) if q_len == 0 else 0,
            "timestamp": datetime.utcnow().isoformat(),
        }))
        last_status_log = now

    logger.debug(f"Queue: {q_len} | Pods: {current}/{MAX_PODS}")

    # -----------------------------------------------------------------------
    # SCALE UP
    # -----------------------------------------------------------------------
    if q_len > 0:
        last_active_time = now
        redis_client.set("last_active_time", str(now))

        needed = min(MAX_PODS, max(1, (q_len + JOBS_PER_POD - 1) // JOBS_PER_POD))

        if needed > current and (now - last_scale_time) > SCALE_UP_COOLDOWN:
            # Check cost guard before scaling
            if not check_cost_guard():
                logger.warning("Scale-up blocked by cost guard")
                return

            try:
                logger.info(f"Scaling up: {current} → {current + 1} pods (need {needed})")
                result = create_pod()
                logger.info(f"Pod created: {result['pod_id']} (cost: ${result.get('cost_per_hr', 0)}/hr)")
                last_scale_time = now
                _record_event(
                    "scale_up",
                    result["pod_id"],
                    f"queue={q_len}, pods={current}→{current + 1}"
                )
            except Exception as e:
                logger.error(f"Failed to create pod: {e}")
                _record_event("scale_up_failed", details=str(e))

    # -----------------------------------------------------------------------
    # SCALE DOWN (full idle shutdown)
    # -----------------------------------------------------------------------
    if q_len == 0 and current > 0:
        idle_time = now - last_active_time

        if idle_time > IDLE_TIMEOUT:
            logger.info(
                f"Idle {idle_time:.0f}s > {IDLE_TIMEOUT}s. "
                f"Terminating all {current} pods → $0"
            )
            _record_event(
                "scale_down",
                details=f"idle={idle_time:.0f}s, terminating {current} pods"
            )

            for pod_id in active_pods[:]:
                try:
                    terminate_pod(pod_id)
                    logger.info(f"Pod terminated: {pod_id}")
                except Exception as e:
                    logger.error(f"Failed to terminate pod {pod_id}: {e}")


# ---------------------------------------------------------------------------
# MAIN LOOP
# ---------------------------------------------------------------------------
def main():
    logger.info("=" * 60)
    logger.info("SimHPC Production Autoscaler v2.2.0")
    logger.info("=" * 60)
    logger.info(
        f"Queue: {QUEUE_NAME} | MAX_PODS: {MAX_PODS} | "
        f"JOBS_PER_POD: {JOBS_PER_POD} | IDLE_TIMEOUT: {IDLE_TIMEOUT}s | "
        f"COOLDOWN: {SCALE_UP_COOLDOWN}s"
    )
    logger.info(
        f"Cost caps: warn=${DAILY_COST_WARN_USD}, hard=${DAILY_COST_HARD_CAP_USD}"
    )

    # Startup health check
    hc = health_check()
    if hc["status"] == "healthy":
        logger.info(
            f"RunPod API: ✓ (account: {hc.get('account_id')}, "
            f"spend/hr: ${hc.get('current_spend_per_hr', 0)})"
        )
    else:
        logger.error(f"RunPod API: ✗ ({hc.get('error')})")
        logger.error("Autoscaler will retry on next cycle")

    while True:
        try:
            scale()
            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            logger.info("Shutting down — terminating all pods...")
            active_pods = _load_pods()
            for pod_id in active_pods[:]:
                try:
                    terminate_pod(pod_id)
                except Exception as e:
                    logger.error(f"Failed to terminate {pod_id}: {e}")
            logger.info("All pods terminated. Goodbye.")
            break
        except Exception as e:
            logger.error(f"Autoscaler error: {e}")
            _record_event("autoscaler_error", details=str(e))
            time.sleep(5)


if __name__ == "__main__":
    main()
