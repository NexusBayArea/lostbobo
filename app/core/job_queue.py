"""
Redis Job Queue with Events, Idempotency, Retry, and DLQ — the wire between API and Worker.

Features:
- Idempotency keys (prevent duplicate jobs)
- Event emission for WebSocket + Autoscaler
- Retry with exponential backoff (optional)
- Dead Letter Queue for failed jobs
- Processing queue for crash recovery
"""

import redis
import json
import uuid
import os
import hashlib

QUEUE_NAME = os.getenv("QUEUE_NAME", "simhpc_jobs")
PROCESSING_QUEUE = os.getenv("PROCESSING_QUEUE", "simhpc_processing")
DLQ_NAME = os.getenv("DLQ_NAME", "simhpc_dlq")
EVENTS_CHANNEL = "jobs:events"

# Retry config
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "5"))
IDEMPOTENCY_TTL = int(os.getenv("IDEMPOTENCY_TTL", "3600"))  # 1 hour

_r = None
_r_event = None


def get_redis():
    global _r
    if _r is None:
        _r = redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True
        )
    return _r


def get_redis_events():
    global _r_event
    if _r_event is None:
        _r_event = redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True
        )
    return _r_event


def publish_event(event_type: str, data: dict):
    """Publish event to Redis pub/sub for WebSocket + autoscaler."""
    event = {"type": event_type, "data": data, "timestamp": int(os.times().real)}
    get_redis_events().publish(EVENTS_CHANNEL, json.dumps(event))


def generate_idempotency_key(user_id: str, payload: dict) -> str:
    """Generate deterministic idempotency key from user_id + payload."""
    raw = f"{user_id}:{json.dumps(payload, sort_keys=True)}"
    return hashlib.sha256(raw.encode()).hexdigest()


def enqueue_job(job_input: any, user_context: dict = None) -> dict:
    """
    Push a job to queue with idempotency check.

    Returns:
        {"status": "queued", "job_id": "..."}
        {"status": "duplicate", "job_id": "existing_id"}
        {"status": "retrying", "job_id": "..."}
    """
    # Handle string input (just job ID)
    if isinstance(job_input, str):
        job_id = job_input
        job_obj = {"id": job_id}
    else:
        job_id = job_input.get("id") or str(uuid.uuid4())
        job_input["id"] = job_id
        job_obj = job_input

    # Add user context if provided
    if user_context:
        job_obj["user_id"] = user_context.get("user_id")
        job_obj["tier"] = user_context.get("tier", "free")
    else:
        job_obj["tier"] = "free"

    # === IDEMPOTENCY CHECK ===
    # Use provided idempotency key or generate from user_id + job content
    idem_key = job_obj.get("idempotency_key")
    if not idem_key and user_context and user_context.get("user_id"):
        idem_key = generate_idempotency_key(user_context.get("user_id"), job_obj)
    if not idem_key:
        idem_key = job_id

    lock_key = f"idem:{idem_key}"
    r = get_redis()

    # SETNX = only set if not exists, with TTL
    was_set = r.set(lock_key, job_id, nx=True, ex=IDEMPOTENCY_TTL)

    if not was_set:
        # Already exists - return existing job ID
        existing_id = r.get(lock_key)
        return {
            "status": "duplicate",
            "job_id": existing_id,
            "message": "Job already queued",
        }

    # === CHECK RETRY STATUS ===
    # If job was previously in DLQ, reset retries
    existing_job = r.get(f"job:{job_id}")
    if existing_job:
        try:
            parsed = json.loads(existing_job)
            if (
                parsed.get("status") == "failed"
                and parsed.get("retries", 0) >= MAX_RETRIES
            ):
                return {
                    "status": "error",
                    "job_id": job_id,
                    "message": "Job already failed max retries",
                }
            # Reset retries for re-queue
            job_obj["retries"] = 0
        except:
            pass

    # === ENQUEUE ===
    payload = json.dumps(job_obj)
    r.lpush(QUEUE_NAME, payload)

    # Also move to processing queue for crash recovery
    r.lpush(PROCESSING_QUEUE, payload)
    r.lrem(QUEUE_NAME, 1, payload)

    # Emit event for WebSocket + autoscaler
    publish_event(
        "job_queued",
        {
            "job_id": job_id,
            "tier": job_obj.get("tier", "free"),
            "user_id": job_obj.get("user_id"),
            "retries": job_obj.get("retries", 0),
        },
    )

    return {"status": "queued", "job_id": job_id}


def mark_processing(raw_job: str) -> str:
    """Move job from processing queue to active processing."""
    r = get_redis()
    r.lrem(PROCESSING_QUEUE, 1, raw_job)
    return raw_job


def complete_job(raw_job: str):
    """Remove job from processing on success."""
    r = get_redis()
    r.lrem(PROCESSING_QUEUE, 1, raw_job)


def move_to_dlq(job_obj: dict, error: str = None):
    """Move failed job to Dead Letter Queue."""
    r = get_redis()
    job_obj["status"] = "failed"
    if error:
        job_obj["error"] = error
    r.lpush(DLQ_NAME, json.dumps(job_obj))
    publish_event("job_dlq", {"job_id": job_obj["id"], "error": error})


def get_dlq(limit: int = 20) -> list:
    """Get jobs from Dead Letter Queue."""
    r = get_redis()
    jobs = r.lrange(DLQ_NAME, 0, limit - 1)
    return [json.loads(j) for j in jobs]


def replay_dlq_job(job_id: str) -> dict:
    """Replay a job from DLQ (reset retries)."""
    r = get_redis()
    jobs = r.lrange(DLQ_NAME, 0, -1)

    for raw in jobs:
        job = json.loads(raw)
        if job.get("id") == job_id:
            # Remove from DLQ
            r.lrem(DLQ_NAME, 1, raw)
            # Reset and re-queue
            job["retries"] = 0
            job.pop("error", None)
            job["status"] = "queued"
            r.lpush(QUEUE_NAME, json.dumps(job))
            publish_event("job_requeued", {"job_id": job_id})
            return {"status": "requeued", "job_id": job_id}

    return {"error": "not found"}


def get_result(job_id: str) -> dict | None:
    """Pull a completed result."""
    raw = get_redis().get(f"jobs:result:{job_id}")
    if raw:
        return json.loads(raw)
    return None
