from typing import Optional

import redis

from app.core.config import settings

# Initialize Redis connection
redis_client = redis.Redis(host="localhost", port=6379, db=0)


def enqueue_job(job_id: str, priority: int = 0) -> None:
    """Enqueue job to appropriate priority queue"""
    # Determine queue based on priority
    if priority >= 10:
        queue_name = settings.QUEUE_HIGH
    elif priority >= 5:
        queue_name = settings.QUEUE_MED
    else:
        queue_name = settings.QUEUE_DEFAULT

    # Push job ID to queue
    redis_client.lpush(queue_name, job_id)


def dequeue_job(timeout: int = 5) -> Optional[str]:
    """Dequeue job from priority queues (high -> med -> default)"""
    # Check queues in priority order
    for queue_name in [settings.QUEUE_HIGH, settings.QUEUE_MED, settings.QUEUE_DEFAULT]:
        job_id = redis_client.brpoplpush(
            queue_name, f"{queue_name}:processing", timeout=timeout
        )
        if job_id:
            return job_id.decode("utf-8") if isinstance(job_id, bytes) else job_id
    return None


def complete_job(job_id: str) -> None:
    """Remove job from processing queue"""
    # Remove from all possible processing queues
    for queue_name in [settings.QUEUE_HIGH, settings.QUEUE_MED, settings.QUEUE_DEFAULT]:
        redis_client.lrem(f"{queue_name}:processing", 1, job_id)
