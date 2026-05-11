# backend/core/kernel/lineage/collector.py
from __future__ import annotations

from typing import Any

from backend.core.kernel.lineage.events import LineageEvent
from backend.core.kernel.lineage.storage import ProvenanceStorage
from backend.core.services.observability_service import observability
from backend.core.tracing import trace_context


class LineageCollector:
    """Unified lineage collector — now uses the new ProvenanceStorage layer."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._storage = ProvenanceStorage.storage()
        return cls._instance

    @classmethod
    def collector(cls) -> LineageCollector:
        return cls()

    async def emit(
        self,
        execution_id: str,
        event_type: str,
        source_type: str,
        source_id: str,
        payload: dict[str, Any],
    ) -> None:
        """Emit lineage event and update provenance graph."""
        with trace_context("lineage.emit") as span:
            event = LineageEvent(
                execution_id=execution_id,
                event_type=event_type,
                source_type=source_type,
                source_id=source_id,
                payload=payload,
            )

            # Store in new provenance storage layer
            await self._storage.store_event(event)

            observability().increment(f"lineage.{event_type}_events")
            span.set_attribute("event_type", event_type)
            span.set_attribute("execution_id", execution_id)
