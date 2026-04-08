"""
Redis Job Queue — the wire between API and Worker.

API pushes JSON to simhpc_jobs
Worker pops JSON, computes, writes to jobs:result:{id}
"""

import redis
import json
import uuid
import os

QUEUE_NAME = os.getenv("QUEUE_NAME", "simhpc_jobs")

_r = None


def get_redis():
    global _r
    if _r is None:
        _r = redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True
        )
    return _r


def enqueue_job(job_input: any) -> str:
    """Push a job ID or full job object to the worker queue."""
    if isinstance(job_input, str):
        # Patch-style: Just push the ID
        job_id = job_input
        payload = job_id
    else:
        # Legacy-style: Generate ID and push object
        job_id = job_input.get("id") or str(uuid.uuid4())
        job_input["id"] = job_id
        payload = json.dumps(job_input)

    get_redis().lpush(QUEUE_NAME, payload)
    return job_id


def get_result(job_id: str) -> dict | None:
    """Pull a completed result. Returns None if still pending."""
    raw = get_redis().get(f"jobs:result:{job_id}")
    if raw:
        return json.loads(raw)
    return None
