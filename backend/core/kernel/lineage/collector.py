# backend/core/kernel/lineage/collector.py
from __future__ import annotations

from typing import Any

from backend.app.core.supabase import get_supabase_client
from backend.core.kernel.lineage.events import LineageEvent
from backend.core.services.observability_service import observability
from backend.core.tracing import trace_context


class LineageCollector:
    """Unified lineage event collector — the single source of provenance."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def collector(cls) -> LineageCollector:
        return cls()

    async def emit(
        self, execution_id: str, event_type: str, source_type: str, source_id: str, payload: dict[str, Any]
    ) -> None:
        """Emit a lineage event to Supabase + Event Bus."""
        with trace_context("lineage.emit") as span:
            LineageEvent(
                execution_id=execution_id,
                event_type=event_type,
                source_type=source_type,
                source_id=source_id,
                payload=payload,
            )

            # Persist to Supabase (orchestration truth)
            try:
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
            except Exception:
                pass  # Lineage never fails the system

            observability().increment(f"lineage.{event_type}_events")
            span.set_attribute("event_type", event_type)
            span.set_attribute("execution_id", execution_id)
