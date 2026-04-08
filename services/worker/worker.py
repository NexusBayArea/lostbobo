#!/usr/bin/env python3
"""
SimHPC Worker (v2.5.8) - PURE COMPUTE ONLY
No FastAPI, no HTTP, no CORS - just Redis queue consumer
"""

import os
import json
import time
import logging
from datetime import datetime
from redis import Redis

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_NAME = os.getenv("QUEUE_NAME", "simhpc_jobs")

redis_client = Redis.from_url(REDIS_URL, decode_responses=True)

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

    for i in range(1, 6):
        job["status"] = "running"
        job["progress"] = i * 20
        job["updated_at"] = int(time.time())

        redis_client.set(f"job:{job_id}", json.dumps(job))
        update_simulation(job_id, {"status": "running", "progress": job["progress"]})
        time.sleep(2)

    job["status"] = "completed"
    job["result"] = {"message": "simulation complete"}
    job["updated_at"] = int(time.time())

    redis_client.set(f"job:{job_id}", json.dumps(job))
    update_simulation(job_id, {"status": "completed", "gpu_result": job["result"]})


def main():
    logger.info("SimHPC Worker v2.5.8 - Pure Compute Mode")

    while True:
        item = redis_client.brpop(QUEUE_NAME, timeout=5)

        if not item:
            continue

        raw_item = item[1]

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
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            job["status"] = "failed"
            job["error"] = str(e)
            job["updated_at"] = int(time.time())
            job["retries"] = job.get("retries", 0) + 1
            redis_client.set(f"job:{job_id}", json.dumps(job))
            update_simulation(job_id, {"status": "failed", "error": str(e)})


if __name__ == "__main__":
    main()
