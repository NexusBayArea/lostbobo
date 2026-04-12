"""
SimHPC Hardened Autoscaler (v2.7.6)
Production-grade elastic scaling for RunPod GPU workers with cost control.
"""

import json
import logging
import os
import time
from datetime import datetime

import requests
from redis import Redis

# --- CONFIG ---
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_NAME = os.getenv("QUEUE_NAME", "simhpc_jobs")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "10"))

# RunPod Config
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
POD_TEMPLATE_ID = os.getenv("RUNPOD_TEMPLATE_ID")

# --- HARD LIMITS & COOLDOWNS ---
MIN_WORKERS = int(os.getenv("MIN_WORKERS", "2"))  # Warm pool: never scale to 0
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "8"))
MIN_WARM_WORKERS = int(os.getenv("MIN_WARM_WORKERS", "2"))  # Always-keep-warm GPUs
SCALE_UP_COOLDOWN = 20  # seconds
SCALE_DOWN_COOLDOWN = 30  # seconds

LAST_SCALE_UP = 0
LAST_SCALE_DOWN = 0

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [AUTOSCALER] %(levelname)s - %(message)s",
)
logger = logging.getLogger("autoscaler")

redis_client = Redis.from_url(REDIS_URL, decode_responses=True)

# --- METRICS ---


def get_queue_depth():
    return redis_client.llen(QUEUE_NAME)


def get_active_workers():
    """Get count of workers currently reporting heartbeats."""
    workers = redis_client.hgetall("sim:workers")
    now = time.time()
    active_count = 0
    for worker_id, last_seen in workers.items():
        if now - float(last_seen) < 30:  # Active within 30s
            active_count += 1
    return active_count


def get_oldest_job_age():
    """Estimate age of the oldest job in the queue (seconds)."""
    # Peek at the tail of the list
    job_raw = redis_client.lindex(QUEUE_NAME, -1)
    if not job_raw:
        return 0
    try:
        job_data = json.loads(job_raw)
        created_at = job_data.get("created_at", time.time())
        return max(0, time.time() - float(created_at))
    except Exception:
        return 0


# --- RUNPOD CONTROL ---


def spawn_worker():
    """Trigger RunPod API to create a new GPU pod."""
    if not RUNPOD_API_KEY or not POD_TEMPLATE_ID:
        logger.error("Missing RUNPOD_API_KEY or RUNPOD_TEMPLATE_ID")
        return None

    logger.info("🚀 Spawning new RunPod worker (idempotent)...")
    url = "https://api.runpod.io/v2/pods"
    payload = {
        "templateId": POD_TEMPLATE_ID,
        "name": f"sim-worker-{int(time.time())}",
        "cloudType": "SECURE",
        "gpuCount": 1,
    }
    headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}"}

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        if resp.status_code == 200:
            pod_id = resp.json().get("id")
            logger.info(f"✅ Spawned pod: {pod_id}")
            # Track pod in Redis for deterministic scale-down
            redis_client.sadd("sim:pods", pod_id)
            return pod_id
        else:
            logger.error(f"❌ RunPod spawn failed: {resp.text}")
            return None
    except Exception as e:
        logger.error(f"Spawn exception: {e}")
        return None


def terminate_worker(pod_id):
    """Trigger RunPod API to terminate a GPU pod."""
    if not RUNPOD_API_KEY:
        return False

    logger.info(f"🧹 Terminating worker pod: {pod_id}")
    url = f"https://api.runpod.io/v2/pods/{pod_id}"
    headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}"}

    try:
        resp = requests.delete(url, headers=headers, timeout=10)
        redis_client.srem("sim:pods", pod_id)
        return resp.status_code == 200
    except Exception as e:
        logger.error(f"Terminate exception: {e}")
        return False


# --- MAINTENANCE ---


def cleanup_stale_workers():
    """Remove workers from the registry that haven't heartbeated in > 60s."""
    workers = redis_client.hgetall("sim:workers")
    now = time.time()
    for worker_id, last_seen in workers.items():
        if now - float(last_seen) > 60:
            logger.info(f"⚠️ removing stale worker {worker_id}")
            redis_client.hdel("sim:workers", worker_id)
            redis_client.srem("workers:active", worker_id)


# --- DECISION ENGINE ---


def get_job_velocity():
    """Calculate average jobs per minute over the last 10 minutes."""
    now = time.time()
    # We use a Redis list to store timestamps of recent jobs
    # This should be populated by the enqueue_job function
    recent_jobs = redis_client.lrange("autoscaler:job_timestamps", 0, -1)
    if not recent_jobs:
        return 0
    
    # Filter for last 600s
    ten_mins_ago = now - 600
    valid_timestamps = [float(t) for t in recent_jobs if float(t) > ten_mins_ago]
    
    # Prune old timestamps from Redis
    if len(valid_timestamps) < len(recent_jobs):
        redis_client.ltrim("autoscaler:job_timestamps", 0, len(valid_timestamps) - 1)
        
    return len(valid_timestamps) / 10.0


def get_desired_workers():
    q = get_queue_depth()
    age = get_oldest_job_age()
    velocity = get_job_velocity()

    # Pressure function (smooth scaling)
    # Added velocity factor for predictive pre-scaling
    pressure = q + (age / 10.0) + (velocity * 2.0)
    target = int(pressure**0.5)

    # Ensure warm pool: keep MIN_WARM_WORKERS always alive
    desired = max(MIN_WORKERS, min(MAX_WORKERS, target))
    desired = max(desired, MIN_WARM_WORKERS)

    return desired


def scale_loop():
    global LAST_SCALE_UP, LAST_SCALE_DOWN

    now = time.time()
    cleanup_stale_workers()

    current = get_active_workers()
    target = get_desired_workers()
    q_depth = get_queue_depth()

    logger.info(f"Hardened Loop: q={q_depth} active={current} target={target}")

    # =====================
    # SCALE UP
    # =====================
    if target > current and (now - LAST_SCALE_UP) > SCALE_UP_COOLDOWN:
        diff = min(target - current, 2)  # burst protection: max 2 at a time
        logger.info(f"📈 Scaling up: +{diff} pods")
        for _ in range(diff):
            spawn_worker()
        LAST_SCALE_UP = now

    # =====================
    # SCALE DOWN (Idle & Excess)
    # =====================
    elif target < current and (now - LAST_SCALE_DOWN) > SCALE_DOWN_COOLDOWN:
        excess = current - target

        # Determine aggressiveness
        if q_depth == 0:
            logger.info("❄️ Queue empty, scaling down aggressively")

        # Get pod IDs tracked in Redis
        pod_ids = list(redis_client.smembers("sim:pods"))

        for pod_id in pod_ids[:excess]:
            terminate_worker(pod_id)

        LAST_SCALE_DOWN = now


def log_status():
    """Log current system status for observability."""
    status = {
        "queue_depth": get_queue_depth(),
        "active_workers": get_active_workers(),
        "target_workers": get_desired_workers(),
        "timestamp": datetime.utcnow().isoformat(),
    }
    redis_client.set("autoscaler:status", json.dumps(status))


def system_ready():
    try:
        return redis_client.ping()
    except Exception:
        return False


def main():
    logger.info("=" * 60)
    logger.info("SimHPC Hardened Autoscaler v2.7.6 — Fail-Safe Control")
    logger.info(
        f"Limits: {MIN_WORKERS}-{MAX_WORKERS} | Cooldowns: {SCALE_UP_COOLDOWN}s/{SCALE_DOWN_COOLDOWN}s"
    )
    logger.info("=" * 60)

    while True:
        try:
            if not system_ready():
                logger.warning("⛔ system (Redis) not ready, skipping")
                time.sleep(5)
                continue

            scale_loop()
            log_status()

            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            logger.info("Shutdown requested")
            break
        except Exception as e:
            logger.error(f"Autoscaler error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
