import asyncio
import logging


import httpx
from app.core.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)

# --- Authority Alignment: Usage Buffer ---
# Buffers usage events for batch flush to Supabase (prevents write pressure)
USAGE_BUFFER: list = []
USAGE_BUFFER_LOCK = asyncio.Lock()


def add_usage_event(
    user_id: str, amount: int, feature_type: str, metadata: dict = None
):
    """
    Add a usage event to the buffer for batch processing.
    Use this instead of direct Supabase writes to prevent write pressure.
    """
    global USAGE_BUFFER
    event = {
        "user_id": user_id,
        "amount": amount,
        "feature_type": feature_type,
        "metadata": metadata or {},
    }
    USAGE_BUFFER.append(event)
    logger.debug(f"Added usage event for user {user_id}: {feature_type}")


async def flush_usage_to_supabase(http_client: httpx.AsyncClient = None):
    """
    Background task: Flushes the usage buffer every 10 seconds to avoid clogging.
    Uses normalized application settings for connectivity.
    """
    global USAGE_BUFFER

    # We use a trick to allow the lifespan to set the client if not provided
    # Or we can just use a local one if needed, but sharing is better.
    client = http_client

    while True:
        await asyncio.sleep(10)  # 10-second heartbeat

        if not USAGE_BUFFER:
            continue

        async with USAGE_BUFFER_LOCK:
            batch_to_send = USAGE_BUFFER.copy()
            USAGE_BUFFER.clear()

        if not batch_to_send:
            continue

        try:
            # Use provided client or create temporary one
            if client:
                response = await client.post(
                    f"{settings.APP_URL}/rest/v1/usage_logs",
                    json=batch_to_send,
                    headers={
                        "apikey": settings.API_TOKEN,
                        "Authorization": f"Bearer {settings.API_TOKEN}",
                        "Content-Type": "application/json",
                        "Prefer": "return=minimal",
                    },
                )
                response.raise_for_status()
                logger.info(f"Flushed {len(batch_to_send)} usage events to Supabase")
            else:
                async with httpx.AsyncClient() as temp_client:
                    response = await temp_client.post(
                        f"{settings.APP_URL}/rest/v1/usage_logs",
                        json=batch_to_send,
                        headers={
                            "apikey": settings.API_TOKEN,
                            "Authorization": f"Bearer {settings.API_TOKEN}",
                            "Content-Type": "application/json",
                            "Prefer": "return=minimal",
                        },
                    )
                    response.raise_for_status()
                    logger.info(
                        f"Flushed {len(batch_to_send)} usage events to Supabase (temp client)"
                    )
        except Exception as e:
            logger.error(f"Batch flush failed: {e}")


async def manual_flush_execution(http_client: httpx.AsyncClient):
    """Manual flush for Vercel Cron or on-demand clearing."""
    global USAGE_BUFFER
    if not USAGE_BUFFER:
        return

    async with USAGE_BUFFER_LOCK:
        batch = USAGE_BUFFER.copy()
        USAGE_BUFFER.clear()

    if not batch:
        return

    if not settings.APP_URL or not settings.API_TOKEN:
        logger.warning("Normalized infrastructure credentials not set, skipping flush")
        return

    try:
        response = await http_client.post(
            f"{settings.APP_URL}/rest/v1/usage_logs",
            json=batch,
            headers={
                "apikey": settings.API_TOKEN,
                "Authorization": f"Bearer {settings.API_TOKEN}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
        )
        response.raise_for_status()
        logger.info(f"Manual flush: {len(batch)} events to Supabase")
    except Exception as e:
        logger.error(f"Manual flush failed: {e}")
