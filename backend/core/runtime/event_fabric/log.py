"""Event Log Service — singleton append-only event fabric."""

from __future__ import annotations

import asyncio
import fnmatch
import hashlib
import json
import logging
from collections.abc import Callable
from typing import Any

from backend.app.core.supabase import get_supabase_client
from backend.core.services.observability_service import observability
from backend.core.services.tracing import tracer

from .schema import SimHPCEvent

log = logging.getLogger(__name__)


def seal_result(data: dict) -> str:
    content = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(content.encode()).hexdigest()


class EventLogService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._supabase = get_supabase_client()
            cls._instance._subscribers: dict[str, list[Callable]] = {}
        return cls._instance

    @classmethod
    def event_log(cls) -> EventLogService:
        return cls()

    async def publish(self, event: SimHPCEvent) -> str:
        sealed = event.seal()
        sealed.provenance_hash = seal_result(sealed.model_dump())

        obs = observability()
        obs.increment(
            "events_published_total",
            {"priority": event.priority, "source": event.source_plugin},
        )

        with tracer.start_as_current_span(
            "event.publish",
            attributes={"event_type": event.event_type},
        ):
            if self._supabase:
                try:
                    self._supabase.table("events").insert(sealed.model_dump()).execute()
                except Exception as exc:
                    log.error("Failed to persist event %s: %s", event.event_id, exc)

        for pattern, handlers in list(self._subscribers.items()):
            if fnmatch.fnmatch(event.event_type, pattern):
                for handler in handlers:
                    asyncio.create_task(self._safe_handler(handler, sealed))

        return sealed.event_id

    async def _safe_handler(self, handler: Callable, event: SimHPCEvent) -> None:
        try:
            await handler(event)
        except Exception as exc:
            log.warning("Event handler error: %s", exc)

    def subscribe(self, event_type_pattern: str, handler: Callable) -> None:
        if event_type_pattern not in self._subscribers:
            self._subscribers[event_type_pattern] = []
        self._subscribers[event_type_pattern].append(handler)

    async def replay(
        self,
        from_ts: float,
        to_ts: float | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 1000,
    ) -> list[SimHPCEvent]:
        if not self._supabase:
            return []

        q = self._supabase.table("events").select("*").gte("timestamp", from_ts)
        if to_ts:
            q = q.lte("timestamp", to_ts)
        if filters:
            for k, v in filters.items():
                q = q.eq(k, v)

        try:
            resp = q.order("timestamp").limit(limit).execute()
            return [SimHPCEvent.model_validate(r) for r in (resp.data or [])]
        except Exception as exc:
            log.error("Event replay failed: %s", exc)
            return []
