"""
Redis Job Queue with Events, Idempotency, Retry, and DLQ — the wire between API and Worker.

Features:
- Idempotency keys (prevent duplicate jobs)
- Event emission for WebSocket + Autoscaler
- Retry with exponential backoff (optional)
- Dead Letter Queue for failed jobs
- Processing queue for crash recovery
"""

import hashlib
import json
import os
import threading
import time
import uuid

import redis

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


def generate_job_fingerprint(user_id: str, job_obj: dict) -> str:
    """Generate a fingerprint of the job's input parameters for coalescing."""
    # Use user_id + input_params for fingerprinting to prevent cross-user coalescing (security)
    # If cross-user coalescing is desired, remove user_id from this.
    data = {
        "user_id": user_id,
        "input_params": job_obj.get("input_params", {}),
        "scenario_name": job_obj.get("scenario_name"),
    }
    raw = json.dumps(data, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def try_push_to_worker(job_obj: dict) -> bool:
    """Attempt to push job directly to an idle worker for sub-second latency."""
    r = get_redis()
    # Get all registered workers
    worker_ids = r.smembers("workers:active")
    
    for wid in worker_ids:
        metadata = r.hgetall(f"worker:metadata:{wid}")
        if metadata.get("status") == "idle":
            url = metadata.get("url")
            if not url:
                continue
            
            try:
                import requests
                resp = requests.post(f"{url}/execute", json=job_obj, timeout=0.5)
                if resp.status_code == 200:
                    publish_event("job_pushed", {"job_id": job_obj["id"], "worker_id": wid})
                    return True
            except Exception as e:
                print(f"[queue] push to worker {wid} failed: {e}")
                
    return False


def enqueue_job(
    job_input: any, user_context: dict = None, async_signal: bool = True
) -> dict:
    """
    Push a job to queue with idempotency check and coalescing.
    """
    # Handle string input (just job ID)
    if isinstance(job_input, str):
        job_id = job_input
        # We need the full object for coalescing, but if only ID provided, we skip coalescing here
        job_obj = {"id": job_id}
    else:
        job_id = job_input.get("id") or str(uuid.uuid4())
        job_input["id"] = job_id
        job_obj = job_input

    # Add user context if provided
    user_id = user_context.get("user_id") if user_context else job_obj.get("user_id")
    if user_context:
        job_obj["user_id"] = user_id
        job_obj["tier"] = user_context.get("tier", "free")
        job_obj["priority"] = user_context.get("priority", 0)
    else:
        job_obj["tier"] = job_obj.get("tier", "free")
        job_obj["priority"] = job_obj.get("priority", 0)

    # === JOB COALESCING ===
    fingerprint = generate_job_fingerprint(user_id, job_obj)
    job_obj["fingerprint"] = fingerprint
    
    r = get_redis()
    coalesce_key = f"coalesce:{fingerprint}"
    
    # Check if a matching job is already queued/running
    existing_job_id = r.get(coalesce_key)
    if existing_job_id:
        # Check if job is still active
        active_status = r.get(f"job:{existing_job_id}:status")
        if active_status in ["queued", "running"]:
            return {
                "status": "coalesced",
                "job_id": existing_job_id,
                "message": "Duplicate compute detected. Coalescing with active job.",
            }

    # Add creation timestamp for autoscaler age tracking
    if "created_at" not in job_obj:
        job_obj["created_at"] = time.time()

    # === IDEMPOTENCY CHECK ===
    # Use provided idempotency key or generate from user_id + job content
    idem_key = job_obj.get("idempotency_key")
    if not idem_key and user_id:
        idem_key = generate_idempotency_key(user_id, job_obj)
    if not idem_key:
        idem_key = job_id

    lock_key = f"idem:{idem_key}"

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

    # Mark as the canonical job for this fingerprint
    r.setex(coalesce_key, 3600, job_id)
    r.setex(f"job:{job_id}:status", 3600, "queued")
    
    # Track for autoscaler predictive scaling
    r.lpush("autoscaler:job_timestamps", time.time())
    r.ltrim("autoscaler:job_timestamps", 0, 500) # Keep last 500 jobs max

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

    # === PUSH DISPATCH (Sub-Second Mode) ===
    # For high priority jobs, try to push directly to an idle worker first
    priority = job_obj.get("priority", 0)
    if priority >= 10:
        if try_push_to_worker(job_obj):
            r.setex(f"job:{job_id}:status", 3600, "running")
            return {"status": "pushed", "job_id": job_id}

    # === ENQUEUE ===
    payload = json.dumps(job_obj)
    
    # Determine queue based on priority
    priority = job_obj.get("priority", 0)
    target_queue = QUEUE_NAME
    if priority >= 10:
        target_queue = f"{QUEUE_NAME}:high"
    elif priority >= 5:
        target_queue = f"{QUEUE_NAME}:med"

    r.lpush(target_queue, payload)

    # Also move to processing queue for crash recovery
    r.lpush(PROCESSING_QUEUE, payload)
    r.lrem(target_queue, 1, payload)

    # === ASYNC SIGNAL (optimization) ===
    # Fire-and-forget Realtime trigger to workers (removes polling delay)
    def _async_signal():
        try:
            # Supabase Realtime channel notification
            # Workers subscribe to this channel for instant job pickup
            get_redis().publish("job:new", json.dumps({"job_id": job_id}))
        except Exception as e:
            print(f"[queue] signal error: {e}")

    if async_signal:
        threading.Thread(target=_async_signal, daemon=True).start()
    else:
        _async_signal()

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
