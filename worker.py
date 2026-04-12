#!/usr/bin/env python3
"""
SimHPC Worker (v2.6.25) - PURE COMPUTE ONLY + Events
Implemented:
- Self-registration
- Heartbeats
- Atomic concurrency counters (O(1))
- Event emission for WebSocket + Autoscaler
- Canonical Job schema (v2.6.11)
"""

import os
import json
import time
import logging
import threading
import uuid
from datetime import datetime
from redis import Redis
from fastapi import FastAPI, BackgroundTasks
import uvicorn

# Import canonical schemas
from app.models.job import Job, JobProgress, JobResult
from app.models.event import JobEvent
from app.core.job_store import serialize_event, now
from app.core.validated_job_store import init_job_store

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
RUNPOD_ENABLED = os.getenv("RUNPOD_ENABLED", "false").lower() == "true"

# Retry config
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "5"))

WORKER_ID = os.getenv("WORKER_ID", f"worker-{uuid.uuid4().hex[:8]}")
POD_IP = os.getenv("RUNPOD_POD_IP", "127.0.0.1")
POD_PORT = os.getenv("WORKER_PORT", "8080")

redis_client = Redis.from_url(REDIS_URL, decode_responses=True)

# Initialize validated job store
job_store = init_job_store(redis_client)


def publish_event(event_type: str, data: dict):
    """Publish canonical event to Redis pub/sub for WebSocket + autoscaler."""
    event = JobEvent(
        type=event_type,
        job_id=data.get("job_id", ""),
        user_id=data.get("user_id"),
        status=data.get("status"),
        progress=data.get("progress"),
        result=data.get("result"),
        error=data.get("error"),
        retries=data.get("retries"),
        timestamp=now(),
    )
    redis_client.publish(EVENTS_CHANNEL, serialize_event(event))


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

    # === EXECUTION IDEMPOTENCY GUARD ===
    # Prevent duplicate execution if already executed
    if redis_client.get(f"job:{job_id}:executed"):
        logger.warning(f"Job {job_id} already executed, skipping")
        return

    # Mark job as executing (with TTL for crash recovery)
    redis_client.setex(f"job:{job_id}:executing", 3600, "1")

    # Mark worker as busy
    redis_client.hset(f"worker:metadata:{WORKER_ID}", "status", "busy")

    # Emit job_started event
    publish_event(
        "job_started",
        {"job_id": job_id, "user_id": user_id, "tier": tier, "worker_id": WORKER_ID},
    )

    try:
        for i in range(1, 6):
            job.status = "running"
            job.progress = JobProgress(percent=i * 20, stage="processing")
            job.updated_at = now()

            job_store.set_job(job)
            update_simulation(
                job_id, {"status": "running", "progress": job.progress.percent}
            )

            publish_event(
                "job_progress",
                {
                    "job_id": job_id,
                    "progress": job.progress.percent,
                    "worker_id": WORKER_ID,
                },
            )

            time.sleep(2)

        job.status = "completed"
        job.result = JobResult(summary="simulation complete", output={})
        job.completed_at = now()
        job.updated_at = now()

        job_store.set_job(job)
        update_simulation(
            job_id, {"status": "completed", "gpu_result": job.result.model_dump()}
        )

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
        # Mark job as executed (prevent re-run after crash recovery)
        if job_id:
            redis_client.setex(f"job:{job_id}:executed", 86400, "1")  # 24h TTL
            redis_client.delete(f"job:{job_id}:executing")
        # Mark worker as idle
        redis_client.hset(f"worker:metadata:{WORKER_ID}", "status", "idle")
        # Decrement active jobs counter (O(1))
        if user_id:
            decrement_active_runs(user_id)


app = FastAPI()


@app.post("/execute")
async def execute_job_push(job_data: dict, background_tasks: BackgroundTasks):
    """Push-based execution endpoint for sub-second latency."""
    job_id = job_data.get("id")
    logger.info(f"🚀 Received push-based job: {job_id}")

    # Validate and process in background to return quickly
    job = Job.model_validate(job_data)
    background_tasks.add_task(process_job, job)

    return {"status": "accepted", "job_id": job_id}


def main():
    logger.info(f"SimHPC Worker v2.7.0 - Worker ID: {WORKER_ID}")

    # 1. Registration
    register_worker()

    # 2. Start Heartbeat Thread
    hb_thread = threading.Thread(target=heartbeat_loop, daemon=True)
    hb_thread.start()

    # 3. Start FastAPI in a separate thread for push-based execution
    def run_api():
        uvicorn.run(app, host="0.0.0.0", port=int(POD_PORT))

    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    logger.info(f"Push-based API listening on port {POD_PORT}")

    while True:
        poll_attempt = 0

        # Priority-aware polling: check high, then med, then default
        queues = [f"{QUEUE_NAME}:high", f"{QUEUE_NAME}:med", QUEUE_NAME]
        raw_item = None

        for q in queues:
            # BRPOPLPUSH is atomic but only for one source.
            # We try each queue with a short timeout.
            raw_item = redis_client.brpoplpush(q, PROCESSING_QUEUE, timeout=1)
            if raw_item:
                break

        if not raw_item:
            poll_attempt += 1
            # Exponential backoff for polling (max 10s)
            sleep_time = min(1.5 * (poll_attempt + 1), 10)
            time.sleep(sleep_time * 0.1)  # Short sleep on timeout
            continue

        try:
            job_data = json.loads(raw_item)
            job_id = job_data.get("id")
            if not job_id:
                logger.error(f"Job missing ID: {job_data}")
                continue

            # Update status in Redis for coalescing logic
            redis_client.setex(f"job:{job_id}:status", 3600, "running")

            job = Job.model_validate(job_data)
            logger.info(f"Processing job: {job_id}")
            process_job(job)

            job_store.set_job(job) if job_store else redis_client.set(
                f"job:{job_id}", job.model_dump_json()
            )
            redis_client.lrem(PROCESSING_QUEUE, 1, raw_item)

        except Exception as e:
            redis_client.lrem(PROCESSING_QUEUE, 1, raw_item)

            logger.error(f"Job {job.id} failed: {e}")
            job.retries = job.retries + 1 if job.retries else 1
            job.error = str(e)
            job.updated_at = int(time.time())

            if job.retries <= MAX_RETRIES:
                logger.warning(f"Retrying job {job.id} ({job.retries}/{MAX_RETRIES})")
                time.sleep(RETRY_DELAY * job.retries)
                redis_client.lpush(QUEUE_NAME, job.model_dump_json())
                update_simulation(
                    job.id,
                    {"status": "retrying", "retries": job.retries, "error": str(e)},
                )
                publish_event(
                    "job_retrying",
                    {
                        "job_id": job.id,
                        "retries": job.retries,
                        "max_retries": MAX_RETRIES,
                    },
                )
            else:
                logger.error(f"Job {job.id} moved to DLQ after {job.retries} attempts")
                job.status = "failed"
                job_store.set_job(job) if job_store else redis_client.set(
                    f"job:{job.id}", job.model_dump_json()
                )
                redis_client.lpush(DLQ_NAME, job.model_dump_json())
                update_simulation(job.id, {"status": "failed", "error": str(e)})
                publish_event(
                    "job_dlq",
                    {"job_id": job.id, "error": str(e), "retries": job.retries},
                )


if __name__ == "__main__":
    main()
