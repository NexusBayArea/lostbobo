#!/usr/bin/env python3
"""
SimHPC Worker (v2.6.25) - PURE COMPUTE ONLY + Events
Implemented:
- Self-registration
- Heartbeats
- Atomic concurrency counters (O(1))
- Event emission for WebSocket + Autoscaler
"""

import os
import json
import time
import logging
import threading
import uuid
from datetime import datetime
from redis import Redis

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- INFRASTRUCTURE CONFIG ---
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_NAME = os.getenv("QUEUE_NAME", "simhpc_jobs")
PROCESSING_QUEUE = os.getenv("PROCESSING_QUEUE", "simhpc_processing")
DLQ_NAME = os.getenv("DLQ_NAME", "simhpc_dlq")
EVENTS_CHANNEL = "jobs:events"

# Retry config
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "5"))

WORKER_ID = os.getenv("WORKER_ID", f"worker-{uuid.uuid4().hex[:8]}")
POD_IP = os.getenv("RUNPOD_POD_IP", "127.0.0.1")
POD_PORT = os.getenv("WORKER_PORT", "8888")

redis_client = Redis.from_url(REDIS_URL, decode_responses=True)


def publish_event(event_type: str, data: dict):
    """Publish event to Redis pub/sub for WebSocket + autoscaler."""
    event = {
        "type": event_type,
        "data": data,
        "worker_id": WORKER_ID,
        "timestamp": int(time.time()),
    }
    redis_client.publish(EVENTS_CHANNEL, json.dumps(event))


# --- SUPABASE CONFIG ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = None

try:
    from supabase import create_client

    if SUPABASE_URL and SUPABASE_SERVICE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        logger.info("Supabase client initialized")
except ImportError:
    logger.warning("Supabase client unavailable")


def register_worker():
    """Register this worker in the active registry."""
    metadata = {
        "worker_id": WORKER_ID,
        "url": f"http://{POD_IP}:{POD_PORT}",
        "gpu": os.getenv("RUNPOD_GPU_ID", "unknown"),
        "status": "idle",
        "last_seen": str(time.time()),
    }
    # Register in the global set
    redis_client.sadd("workers:active", WORKER_ID)
    # Store metadata
    redis_client.hset(f"worker:metadata:{WORKER_ID}", mapping=metadata)
    logger.info(f"Worker {WORKER_ID} registered successfully at {metadata['url']}")


def heartbeat_loop():
    """Background loop to update heartbeat key in Redis."""
    while True:
        try:
            # Update metadata last_seen
            redis_client.hset(
                f"worker:metadata:{WORKER_ID}", "last_seen", str(time.time())
            )
            # Set a TTL-based heartbeat key for pruning
            redis_client.setex(f"worker:heartbeat:{WORKER_ID}", 30, "alive")
            time.sleep(10)
        except Exception as e:
            logger.error(f"Heartbeat failed: {e}")
            time.sleep(5)


def decrement_active_runs(user_id: str):
    """Decrement the active runs counter for a user."""
    try:
        # Ensure it doesn't go below 0
        val = redis_client.decr(f"user:{user_id}:active_runs")
        if val < 0:
            redis_client.set(f"user:{user_id}:active_runs", "0")
    except Exception as e:
        logger.error(f"Failed to decrement active runs: {e}")


def update_simulation(job_id: str, data: dict):
    if not supabase:
        return
    try:
        data["updated_at"] = datetime.utcnow().isoformat()
        supabase.table("simulations").update(data).eq("job_id", job_id).execute()
    except Exception as e:
        logger.error(f"Supabase sync failed: {e}")


def process_job(job):
    job_id = job.get("id")
    user_id = job.get("user_id")
    tier = job.get("tier", "free")

    # Mark worker as busy
    redis_client.hset(f"worker:metadata:{WORKER_ID}", "status", "busy")

    # Emit job_started event
    publish_event(
        "job_started",
        {"job_id": job_id, "user_id": user_id, "tier": tier, "worker_id": WORKER_ID},
    )

    try:
        for i in range(1, 6):
            job["status"] = "running"
            job["progress"] = i * 20
            job["updated_at"] = int(time.time())

            redis_client.set(f"job:{job_id}", json.dumps(job))
            update_simulation(
                job_id, {"status": "running", "progress": job["progress"]}
            )

            # Emit job_progress event
            publish_event(
                "job_progress",
                {"job_id": job_id, "progress": job["progress"], "worker_id": WORKER_ID},
            )

            time.sleep(2)

        job["status"] = "completed"
        job["result"] = {"message": "simulation complete"}
        job["updated_at"] = int(time.time())

        redis_client.set(f"job:{job_id}", json.dumps(job))
        update_simulation(job_id, {"status": "completed", "gpu_result": job["result"]})

        # Emit job_completed event
        publish_event(
            "job_completed",
            {"job_id": job_id, "result": job["result"], "worker_id": WORKER_ID},
        )

    except Exception as e:
        # Emit job_failed event
        publish_event(
            "job_failed", {"job_id": job_id, "error": str(e), "worker_id": WORKER_ID}
        )
        raise

    finally:
        # Mark worker as idle
        redis_client.hset(f"worker:metadata:{WORKER_ID}", "status", "idle")
        # Decrement active jobs counter (O(1))
        if user_id:
            decrement_active_runs(user_id)


def main():
    logger.info(f"SimHPC Worker v2.6.23 - Worker ID: {WORKER_ID}")

    # 1. Registration
    register_worker()

    # 2. Start Heartbeat Thread
    hb_thread = threading.Thread(target=heartbeat_loop, daemon=True)
    hb_thread.start()

    while True:
        # Use BRPOPLPUSH for crash recovery - move to processing queue
        raw_item = redis_client.brpoplpush(QUEUE_NAME, PROCESSING_QUEUE, timeout=5)

        if not raw_item:
            continue

        try:
            job = json.loads(raw_item)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in queue: {raw_item}")
            continue

        job_id = job.get("id")
        if not job_id:
            logger.error(f"Job missing ID: {job}")
            continue

        try:
            logger.info(f"Processing job: {job_id}")
            process_job(job)
            # Success - remove from processing queue
            redis_client.lrem(PROCESSING_QUEUE, 1, raw_item)

        except Exception as e:
            # Failure - remove from processing queue
            redis_client.lrem(PROCESSING_QUEUE, 1, raw_item)

            logger.error(f"Job {job_id} failed: {e}")
            retries = job.get("retries", 0) + 1
            job["retries"] = retries
            job["error"] = str(e)
            job["updated_at"] = int(time.time())

            if retries <= MAX_RETRIES:
                # Retry - put back in queue with delay
                logger.warning(f"Retrying job {job_id} ({retries}/{MAX_RETRIES})")
                time.sleep(RETRY_DELAY * retries)  # Exponential backoff
                redis_client.lpush(QUEUE_NAME, json.dumps(job))
                update_simulation(
                    job_id, {"status": "retrying", "retries": retries, "error": str(e)}
                )
                publish_event(
                    "job_retrying",
                    {"job_id": job_id, "retries": retries, "max_retries": MAX_RETRIES},
                )
            else:
                # Max retries exceeded - move to DLQ
                logger.error(f"Job {job_id} moved to DLQ after {retries} attempts")
                job["status"] = "failed"
                redis_client.set(f"job:{job_id}", json.dumps(job))
                # Move to DLQ
                redis_client.lpush(DLQ_NAME, json.dumps(job))
                update_simulation(job_id, {"status": "failed", "error": str(e)})
                publish_event(
                    "job_dlq", {"job_id": job_id, "error": str(e), "retries": retries}
                )


if __name__ == "__main__":
    main()
