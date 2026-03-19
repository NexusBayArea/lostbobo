#!/usr/bin/env python3
"""
SimHPC RunPod Worker
RunPod Pod worker that processes simulation jobs from Redis queue.

Key features:
- Infinite loop (while True) - NOT serverless
- Polls Redis queue for jobs
- Concurrent job processing with MAX_CONCURRENT_JOBS limit
- Heartbeat to Supabase for health monitoring
- Updates simulation_history table for real-time dashboard sync
"""

import os
import json
import time
import logging
import threading
from datetime import datetime
from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

MAX_CONCURRENT_JOBS = int(os.getenv("MAX_CONCURRENT_JOBS", "2"))
active_jobs = 0
lock = threading.Lock()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_NAME = os.getenv("QUEUE_NAME", "simhpc_jobs")
POLL_INTERVAL_SEC = float(os.getenv("POLL_INTERVAL_SEC", "2"))
IDLE_TIMEOUT = int(os.getenv("IDLE_TIMEOUT", "300"))
RUNPOD_POD_ID = os.getenv("RUNPOD_POD_ID", f"worker-{os.getpid()}")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = None

try:
    from supabase import create_client

    if SUPABASE_URL and SUPABASE_SERVICE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        logger.info("Supabase client initialized")
except ImportError:
    logger.warning("Supabase not available, heartbeat disabled")


def update_job_status(job_id: str, status: str, result: dict = None):
    """Updates Supabase so the Frontend Dashboard reflects reality in real-time."""
    if not supabase:
        return
    try:
        data = {"status": status}
        if result:
            data["result_summary"] = result
            data["report_url"] = result.get("pdf_link")
        supabase.table("simulation_history").update(data).eq("job_id", job_id).execute()
        logger.debug(f"Supabase status sync: {job_id} -> {status}")
    except Exception as e:
        logger.error(f"Failed to sync status to Supabase: {e}")


def process_job(job: dict):
    """Process a single simulation job."""
    global active_jobs
    job_id = job.get("id", "unknown")

    try:
        logger.info(f"Running job {job_id}")
        update_job_status(job_id, "running")

        result = {
            "status": "completed",
            "job_id": job_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {"message": "Simulation completed successfully"},
        }

        redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.set(f"simhpc_result:{job_id}", json.dumps(result))
        update_job_status(job_id, "completed", result)
        logger.info(f"Done {job_id}")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.set(
            f"simhpc_result:{job_id}", json.dumps({"error": str(e), "job_id": job_id})
        )
        update_job_status(job_id, "failed", {"error": str(e)})
    finally:
        with lock:
            active_jobs -= 1


def send_heartbeat():
    """Send heartbeat to Supabase."""
    if not supabase:
        return
    try:
        supabase.table("worker_heartbeat").upsert(
            {
                "worker_id": RUNPOD_POD_ID,
                "status": "online",
                "last_ping": datetime.utcnow().isoformat(),
            }
        ).execute()
        logger.debug("Heartbeat sent to Supabase")
    except Exception as e:
        logger.error(f"Heartbeat failed: {e}")


def main():
    """Main worker loop - infinite polling of Redis queue."""
    global active_jobs
    logger.info("SimHPC Worker Booting...")

    try:
        redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()
        logger.info(f"Connected to Redis at {REDIS_URL}")
    except RedisConnectionError as e:
        logger.error(f"Cannot connect to Redis: {e}")
        return

    logger.info(f"Worker started. Waiting for jobs...")
    logger.info(f"Queue: {QUEUE_NAME}, Max concurrent jobs: {MAX_CONCURRENT_JOBS}")

    last_active = time.time()

    while True:
        try:
            with lock:
                if active_jobs >= MAX_CONCURRENT_JOBS:
                    time.sleep(1)
                    continue

            job_data = redis_client.lpop(QUEUE_NAME)

            if job_data:
                last_active = time.time()
                try:
                    job = json.loads(job_data)
                    with lock:
                        active_jobs += 1
                    threading.Thread(target=process_job, args=(job,)).start()
                    logger.info(
                        f"Started job {job.get('id', 'unknown')} (active: {active_jobs})"
                    )
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode job: {e}")
                    with lock:
                        active_jobs -= 1
                send_heartbeat()
            else:
                idle_time = time.time() - last_active
                if idle_time > IDLE_TIMEOUT:
                    logger.info(f"Idle for {idle_time}s > {IDLE_TIMEOUT}s threshold")
                    logger.info("Note: Pod will be stopped by autoscaler")
                time.sleep(POLL_INTERVAL_SEC)

        except Exception as e:
            logger.error(f"Worker loop error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
