"""Supabase Job Store — replaces Redis for queuing, streaming, and pub/sub."""

from __future__ import annotations

import logging
import time
from typing import Any

from backend.app.core.supabase import get_supabase_client

log = logging.getLogger(__name__)


class SupabaseJobStore:
    """Supabase-based replacement for Redis Streams + Pub/Sub."""

    def __init__(self):
        self.client = None

    async def connect(self):
        if not self.client:
            self.client = get_supabase_client()
            if self.client:
                log.info("Supabase Job Store connected")
            else:
                log.warning("Supabase client unavailable - running in mock mode")

    async def enqueue(self, queue: str, payload: dict[str, Any]) -> str:
        """Enqueue job to queue (replaces Redis XADD)."""
        await self.connect()
        if not self.client:
            return f"mock_job_{int(time.time() * 1000)}"

        job_id = f"job_{int(time.time() * 1000)}"
        await (
            self.client.table("jobs")
            .insert(
                {
                    "job_id": job_id,
                    "queue": queue,
                    "status": "pending",
                    "payload": payload,
                }
            )
            .execute()
        )

        log.info(f"Enqueued {job_id} to {queue}")
        return job_id

    async def dequeue(self, queue: str, limit: int = 1) -> list[dict]:
        """Dequeue pending jobs (replaces Redis XRANGE)."""
        await self.connect()
        if not self.client:
            return []

        resp = (
            await self.client.table("jobs")
            .select("*")
            .eq("queue", queue)
            .eq("status", "pending")
            .order("created_at")
            .limit(limit)
            .execute()
        )

        return resp.data or []

    async def publish(self, channel: str, event: dict[str, Any]):
        """Publish event to channel (replaces Redis PUBLISH)."""
        await self.connect()
        if not self.client:
            return

        await (
            self.client.table("events")
            .insert(
                {
                    "channel": channel,
                    "event_type": event.get("event", "update"),
                    "payload": event,
                }
            )
            .execute()
        )

    async def subscribe(self, channel: str):
        """Placeholder for Supabase Realtime subscription."""
        log.info(f"Subscribed to channel: {channel} (Supabase Realtime)")

    async def update_job(self, job_id: str, status: str, result: dict[str, Any] | None = None):
        """Update job status (replaces Redis HSET)."""
        await self.connect()
        if not self.client:
            return

        update = {"status": status}
        if result:
            update["result"] = result
        await self.client.table("jobs").update(update).eq("job_id", job_id).execute()

    async def get_job(self, job_id: str) -> dict | None:
        """Get job by ID."""
        await self.connect()
        if not self.client:
            return None

        resp = await self.client.table("jobs").select("*").eq("job_id", job_id).execute()
        return resp.data[0] if resp.data else None
