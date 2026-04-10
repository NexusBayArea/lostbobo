import json
import asyncio
import logging
from redis import Redis
from app.core.ws_manager import manager

logger = logging.getLogger(__name__)

EVENTS_CHANNEL = "jobs:events"


def start_event_listener(redis: Redis):
    """Start Redis pub/sub listener in background thread."""
    pubsub = redis.pubsub()
    pubsub.subscribe(EVENTS_CHANNEL)

    logger.info("WebSocket event listener started")

    def listen():
        for message in pubsub.listen():
            if message["type"] != "message":
                continue

            try:
                data = json.loads(message["data"])
                event_type = data.get("type")
                payload = data.get("data", {})
                job_id = payload.get("job_id")

                if not job_id:
                    continue

                # Run async broadcast in event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(
                        manager.broadcast(
                            job_id,
                            {
                                "type": event_type,
                                "data": payload,
                                "timestamp": data.get("timestamp"),
                            },
                        )
                    )
                finally:
                    loop.close()

            except Exception as e:
                logger.error(f"Event listener error: {e}")

    import threading

    listener_thread = threading.Thread(target=listen, daemon=True)
    listener_thread.start()
    return listener_thread
