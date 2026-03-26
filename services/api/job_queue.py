"""
Redis Job Queue — the wire between API and Worker.

API pushes JSON to  jobs:pending
Worker pops JSON, computes, writes to  jobs:result:{id}
"""

import redis
import json
import uuid
import os

r = redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True
)


def enqueue_job(payload: dict) -> str:
    """Push a job to the worker queue. Returns job_id."""
    job_id = str(uuid.uuid4())

    job = {
        "id": job_id,
        "payload": payload,
        "status": "pending",
    }

    r.lpush("jobs:pending", json.dumps(job))
    return job_id


def get_result(job_id: str) -> dict | None:
    """Pull a completed result. Returns None if still pending."""
    raw = r.get(f"jobs:result:{job_id}")
    if raw:
        return json.loads(raw)
    return None
