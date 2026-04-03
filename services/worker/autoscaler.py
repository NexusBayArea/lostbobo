"""
SimHPC Autoscaler — Option C (v2.3.0)
On-demand Pod + Network Volume + Stop/Resume strategy.

WHAT THIS DOES:
  - Queue has jobs   → resume stopped pod (or create if none exists)
  - Queue empty      → STOP pod after IDLE_TIMEOUT (keeps disk, ~$0.10/day)
  - NEVER terminate  → pod is yours, nobody can steal it
  - Network Volume   → /workspace persists even across pod recreations

COST AT 4 ACTIVE HOURS/DAY (A40):
  Running:  4hr  × $0.39  = $1.56/day
  Stopped: 20hr  × $0.005 = $0.10/day  (disk only)
  Volume:  20GB  × flat   = $0.20/day
  TOTAL:                  ≈ $1.86/day  (~$56/month)

DEMO READINESS:
  Call POST /api/v1/admin/fleet/warm before a demo.
  Pod wakes in ~90 seconds. By the time intros are done, it's ready.
"""

import os
import json
import time
import logging
from datetime import datetime

import redis
from runpod_api import (
    list_pods,
    create_pod,
    stop_pod,
    start_pod,
    health_check,
    _load_pods,
    _save_pods,
    _record_event,
    _update_cost_tracking,
    MAX_PODS,
    JOBS_PER_POD,
    SCALE_UP_COOLDOWN,
    DEFAULT_GPU_TYPE,
)

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
REDIS_URL        = os.getenv("REDIS_URL",      "redis://localhost:6379/0")
QUEUE_NAME       = os.getenv("QUEUE_NAME",     "simhpc_jobs")
CHECK_INTERVAL   = int(os.getenv("CHECK_INTERVAL",   "15"))
IDLE_TIMEOUT     = int(os.getenv("IDLE_TIMEOUT",     "300"))   # 5 min

# Cost guards
DAILY_WARN_USD   = float(os.getenv("DAILY_COST_WARN_USD",     "5.0"))
DAILY_CAP_USD    = float(os.getenv("DAILY_COST_HARD_CAP_USD", "15.0"))

# Network Volume config (set in RunPod dashboard, referenced here for logs)
NETWORK_VOLUME_MOUNT = os.getenv("NETWORK_VOLUME_MOUNT", "/workspace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [AUTOSCALER] %(levelname)s - %(message)s",
)
logger = logging.getLogger("autoscaler")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# ---------------------------------------------------------------------------
# STATE
# ---------------------------------------------------------------------------
last_scale_time  = 0
last_active_time = time.time()
last_status_log  = 0
STATUS_LOG_INTERVAL = 60


# ---------------------------------------------------------------------------
# SYNC
# ---------------------------------------------------------------------------
def sync_pods() -> tuple[list[str], list[str]]:
    """
    Returns (running_ids, stopped_ids).
    Writes stopped list to Redis so the warm endpoint can find it.
    """
    try:
        all_pods   = list_pods()
        running    = [p["pod_id"] for p in all_pods if p["status"] == "RUNNING"]
        stopped    = [p["pod_id"] for p in all_pods if p["status"] == "STOPPED"]

        _save_pods(running)
        redis_client.set("pods:stopped", json.dumps(stopped))
        return running, stopped

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        running = _load_pods()
        stopped = json.loads(redis_client.get("pods:stopped") or "[]")
        return running, stopped


# ---------------------------------------------------------------------------
# COST GUARD
# ---------------------------------------------------------------------------
def check_cost_guard() -> bool:
    today = float(redis_client.get("cost:today_usd") or 0)
    if today >= DAILY_CAP_USD:
        logger.critical(f"COST CAP: ${today:.2f} >= ${DAILY_CAP_USD:.2f}. Blocking scale-up.")
        _record_event("cost_cap_reached", details=f"${today:.2f}")
        return False
    if today >= DAILY_WARN_USD:
        logger.warning(f"COST WARN: ${today:.2f} / ${DAILY_CAP_USD:.2f}")
    return True


# ---------------------------------------------------------------------------
# WARM (called by API /fleet/warm endpoint before demos)
# ---------------------------------------------------------------------------
def warm_pod() -> dict:
    """
    Resume a stopped pod immediately, bypassing idle timer.
    Called proactively before demos so pod is ready when needed.
    Returns status dict the API endpoint can return directly.
    """
    running, stopped = sync_pods()

    if running:
        return {
            "status": "already_running",
            "pod_id": running[0],
            "message": "Pod is already running and ready.",
        }

    if stopped:
        pod_id = stopped[0]
        try:
            result = start_pod(pod_id)
            _record_event("pod_warmed", pod_id, "pre-demo warm request")
            logger.info(f"WARM: Resumed pod {pod_id} for demo")
            return {
                "status": "warming",
                "pod_id": pod_id,
                "message": "Pod resuming — ready in ~90 seconds.",
                "cost_per_hr": result.get("cost_per_hr", 0.39),
            }
        except Exception as e:
            logger.error(f"WARM: Failed to resume {pod_id}: {e}")
            return {"status": "error", "message": str(e)}

    # No pod at all — create one fresh
    if not check_cost_guard():
        return {"status": "error", "message": "Daily cost cap reached."}
    try:
        result = create_pod()
        _record_event("pod_warmed_new", result["pod_id"], "warm created new pod")
        logger.info(f"WARM: Created new pod {result['pod_id']} for demo")
        return {
            "status": "creating",
            "pod_id": result["pod_id"],
            "message": "No stopped pod found — creating fresh pod. Ready in ~3 minutes.",
            "cost_per_hr": result.get("cost_per_hr", 0.39),
        }
    except Exception as e:
        logger.error(f"WARM: Failed to create pod: {e}")
        return {"status": "error", "message": str(e)}


# ---------------------------------------------------------------------------
# SCALING LOOP
# ---------------------------------------------------------------------------
def scale():
    global last_scale_time, last_active_time, last_status_log

    q_len              = redis_client.llen(QUEUE_NAME)
    running, stopped   = sync_pods()
    current            = len(running)

    # Charge cost only for running pods (stopped = disk only ≈ free)
    _update_cost_tracking(current, DEFAULT_GPU_TYPE)

    now = time.time()

    # Periodic status snapshot for admin dashboard
    if now - last_status_log > STATUS_LOG_INTERVAL:
        today_cost = float(redis_client.get("cost:today_usd") or 0)
        hourly     = current * 0.39
        idle_sec   = round(now - last_active_time, 1) if q_len == 0 else 0

        logger.info(
            f"Fleet: {current} running / {len(stopped)} stopped | "
            f"Queue: {q_len} | ${hourly:.3f}/hr | ${today_cost:.3f} today"
        )
        redis_client.set("autoscaler:last_status", json.dumps({
            "running_pods":  current,
            "stopped_pods":  len(stopped),
            "stopped_ids":   stopped,
            "max_pods":      MAX_PODS,
            "queue":         q_len,
            "cost_hourly":   round(hourly, 4),
            "cost_today":    round(today_cost, 4),
            "idle_sec":      idle_sec,
            "idle_timeout":  IDLE_TIMEOUT,
            "volume_mount":  NETWORK_VOLUME_MOUNT,
            "timestamp":     datetime.utcnow().isoformat(),
        }))
        last_status_log = now

    # ── SCALE UP ──────────────────────────────────────────────────────────
    if q_len > 0:
        last_active_time = now
        redis_client.set("last_active_time", str(now))

        needed = min(MAX_PODS, max(1, (q_len + JOBS_PER_POD - 1) // JOBS_PER_POD))

        if needed > current and (now - last_scale_time) > SCALE_UP_COOLDOWN:
            if not check_cost_guard():
                return

            # Prefer resuming stopped pod — faster and cheaper than new creation
            if stopped:
                pod_id = stopped[0]
                try:
                    result = start_pod(pod_id)
                    logger.info(f"Resumed pod {pod_id} (queue={q_len})")
                    last_scale_time = now
                    _record_event("pod_resumed", pod_id, f"queue={q_len}")
                except Exception as e:
                    logger.error(f"Resume failed for {pod_id}: {e}")
                    _record_event("pod_resume_failed", pod_id, str(e))

            # No stopped pods — create fresh (mounts Network Volume automatically)
            elif current < MAX_PODS:
                try:
                    result = create_pod()
                    logger.info(
                        f"Created pod {result['pod_id']} — "
                        f"Network Volume will mount at {NETWORK_VOLUME_MOUNT}"
                    )
                    last_scale_time = now
                    _record_event("pod_created", result["pod_id"], f"queue={q_len}")
                except Exception as e:
                    logger.error(f"Create pod failed: {e}")
                    _record_event("pod_create_failed", details=str(e))

    # ── SCALE DOWN (STOP, not terminate) ──────────────────────────────────
    if q_len == 0 and current > 0:
        idle_sec = now - last_active_time

        if idle_sec > IDLE_TIMEOUT:
            logger.info(
                f"Idle {idle_sec:.0f}s > {IDLE_TIMEOUT}s — STOPPING {current} pods "
                f"(disk preserved, cost ~$0.005/hr)"
            )
            _record_event("scale_down_stop", details=f"idle={idle_sec:.0f}s, pods={current}")

            for pod_id in running[:]:
                try:
                    stop_pod(pod_id)          # ← STOP not terminate
                    logger.info(
                        f"Pod STOPPED: {pod_id} "
                        f"(Network Volume intact, resumes in ~90s on next job)"
                    )
                    _record_event("pod_stopped", pod_id, "idle — disk + volume preserved")
                except Exception as e:
                    logger.error(f"Failed to stop {pod_id}: {e}")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    logger.info("=" * 60)
    logger.info("SimHPC Autoscaler v2.3.0 — Option C: On-demand + Network Volume")
    logger.info("=" * 60)
    logger.info(f"Strategy: STOP on idle (never terminate)")
    logger.info(f"Idle timeout: {IDLE_TIMEOUT}s | Max pods: {MAX_PODS}")
    logger.info(f"Cost caps: warn=${DAILY_WARN_USD} / hard=${DAILY_CAP_USD}")
    logger.info(f"Network Volume mount: {NETWORK_VOLUME_MOUNT}")
    logger.info(f"Estimated idle cost: ~$0.10/day (disk) + $0.20/day (volume)")

    hc = health_check()
    if hc["status"] == "healthy":
        logger.info(f"RunPod API: OK (spend/hr: ${hc.get('current_spend_per_hr', 0):.3f})")
    else:
        logger.error(f"RunPod API: FAIL — {hc.get('error')}")

    while True:
        try:
            scale()
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            logger.info("Shutdown — stopping all running pods (disk preserved)...")
            running, _ = sync_pods()
            for pod_id in running:
                try:
                    stop_pod(pod_id)
                    logger.info(f"Stopped on shutdown: {pod_id}")
                except Exception as e:
                    logger.error(f"Stop failed for {pod_id}: {e}")
            logger.info("Done. All pods stopped, Network Volume intact.")
            break
        except Exception as e:
            logger.error(f"Autoscaler error: {e}")
            _record_event("autoscaler_error", details=str(e))
            time.sleep(5)


if __name__ == "__main__":
    main()
