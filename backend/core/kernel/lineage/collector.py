# backend/core/kernel/lineage/collector.py
from __future__ import annotations

from typing import Any

from backend.app.core.supabase import get_supabase_client
from backend.core.kernel.lineage.events import LineageEvent
from backend.core.services.observability_service import observability
from backend.core.tracing import trace_context


class LineageCollector:
    """Unified lineage event collector."""

    _instance: LineageCollector | None = None

    @classmethod
    def collector(cls) -> LineageCollector:
        if cls._instance is None:
            cls._instance = LineageCollector()
        return cls._instance

    async def emit(
        self,
        execution_id: str,
        event_type: str,
        source_type: str,
        source_id: str,
        payload: dict[str, Any],
    ):
        """Emit a lineage event."""
        with trace_context("lineage.emit") as span:
            _ = LineageEvent(
                execution_id=execution_id,
                event_type=event_type,
                source_type=source_type,
                source_id=source_id,
                payload=payload,
            )

            await (
                get_supabase_client()
                .table("execution_lineage")
                .insert(
                    {
                        "execution_id": execution_id,
                        "event_type": event_type,
                        "source_type": source_type,
                        "source_id": source_id,
                        "payload": payload,
                    }
                )
                .execute()
            )

            observability().increment(f"lineage.{event_type}_events")
            span.set_attribute("event_type", event_type)
            span.set_attribute("execution_id", execution_id)
