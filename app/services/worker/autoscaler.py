"""
SimHPC Autoscaler — Single-Pod Event-Driven Mode (v2.6.25)
Reacts to Redis pub/sub events instead of polling queue.
"""

import os
import time
import json
import logging
import threading
from datetime import datetime
from redis import Redis

# --- CONFIG ---
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_NAME = os.getenv("QUEUE_NAME", "simhpc_jobs")
EVENTS_CHANNEL = "jobs:events"
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "10"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [AUTOSCALER] %(levelname)s - %(message)s",
)
logger = logging.getLogger("autoscaler")

redis_client = Redis.from_url(REDIS_URL, decode_responses=True)

# --- EVENT HANDLERS ---
last_scale_time = 0


def handle_job_queued(event_data):
    """React to job_queued event."""
    global last_scale_time
    queue_depth = redis_client.llen(QUEUE_NAME)
    logger.info(f"Event: job_queued → queue_depth={queue_depth}")
    # In single-pod mode, no scaling needed


def handle_job_completed(event_data):
    """React to job_completed event."""
    queue_depth = redis_client.llen(QUEUE_NAME)
    logger.info(f"Event: job_completed → queue_depth={queue_depth}")


def handle_job_failed(event_data):
    """React to job_failed event."""
    logger.warning(f"Event: job_failed → job_id={event_data.get('job_id')}")


def handle_event(message):
    """Process incoming Redis pub/sub event."""
    try:
        data = json.loads(message["data"])
        event_type = data.get("type")
        event_data = data.get("data", {})

        if event_type == "job_queued":
            handle_job_queued(event_data)
        elif event_type == "job_completed":
            handle_job_completed(event_data)
        elif event_type == "job_failed":
            handle_job_failed(event_data)
        else:
            logger.debug(f"Ignored event type: {event_type}")

    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in event: {message}")
    except Exception as e:
        logger.error(f"Event handler error: {e}")


def log_status():
    """Log current system status for observability."""
    queue_depth = redis_client.llen(QUEUE_NAME)
    active_jobs = redis_client.hlen("jobs:active")
    worker_alive = redis_client.get("worker:heartbeat")

    status = {
        "mode": "single-pod-event-driven",
        "queue_depth": queue_depth,
        "active_jobs": active_jobs,
        "worker_alive": worker_alive is not None,
        "timestamp": datetime.utcnow().isoformat(),
    }

    logger.info(
        f"[Single-Pod] queue={queue_depth} active_jobs={active_jobs} worker={'alive' if worker_alive else 'dead'}"
    )
    redis_client.set("autoscaler:status", json.dumps(status))


def event_listener():
    """Subscribe to Redis pub/sub and process events."""
    pubsub = redis_client.pubsub()
    pubsub.subscribe(EVENTS_CHANNEL)

    logger.info(f"Subscribed to {EVENTS_CHANNEL} for event-driven updates")

    for message in pubsub.listen():
        if message["type"] == "message":
            handle_event(message)


def system_ready():
    """Check if the system (Redis) is reachable."""
    try:
        return redis_client.ping()
    except Exception:
        return False


def main():
    logger.info("=" * 60)
    logger.info("SimHPC Autoscaler v2.7.2 — Single-Pod Event-Driven")
    logger.info("Mode: Event-driven (no polling)")
    logger.info("Function: React to job_queued/completed/failed events")
    logger.info("=" * 60)

    # Start event listener in background thread
    event_thread = threading.Thread(target=event_listener, daemon=True)
    event_thread.start()

    # Main loop for periodic status logging
    while True:
        try:
            if not system_ready():
                logger.warning("⛔ system (Redis) not ready, skipping scaling/logging")
                time.sleep(5)
                continue

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
