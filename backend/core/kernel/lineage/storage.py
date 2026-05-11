# backend/core/kernel/lineage/storage.py
from __future__ import annotations

import hashlib
import json
from typing import Any

from backend.app.core.supabase import get_supabase_client
from backend.core.kernel.lineage.events import LineageEvent
from backend.core.services.observability_service import observability
from backend.core.tracing import trace_context


class ProvenanceStorage:
    """Unified provenance storage layer."""

    _instance: ProvenanceStorage | None = None

    @classmethod
    def storage(cls) -> ProvenanceStorage:
        if cls._instance is None:
            cls._instance = ProvenanceStorage()
        return cls._instance

    async def store_event(self, event: LineageEvent) -> None:
        """Store raw lineage event + update graph."""
        with trace_context("provenance.store_event") as span:
            # 1. Store raw event
            await (
                get_supabase_client()
                .table("execution_lineage")
                .insert(
                    {
                        "execution_id": event.execution_id,
                        "event_type": event.event_type,
                        "source_type": event.source_type,
                        "source_id": event.source_id,
                        "payload": event.payload,
                        "trace_id": event.payload.get("trace_id", ""),
                        "correlation_id": event.payload.get("correlation_id", ""),
                        "causation_id": event.payload.get("causation_id", ""),
                    }
                )
                .execute()
            )

            # 2. Update provenance graph (nodes + edges)
            await self._update_graph(event)

            observability().increment("provenance_events_stored")
            span.set_attribute("execution_id", event.execution_id)

    async def _update_graph(self, event: LineageEvent):
        """Maintain the provenance graph in real time."""
        node_id = f"{event.source_type}:{event.source_id}"

        # Insert node
        await (
            get_supabase_client()
            .table("provenance_nodes")
            .upsert(
                {
                    "execution_id": event.execution_id,
                    "node_type": event.source_type,
                    "node_name": event.source_id,
                    "metadata": event.payload,
                },
                on_conflict="execution_id,node_type,node_name",
            )
            .execute()
        )

        # Insert edge to execution root
        await (
            get_supabase_client()
            .table("provenance_edges")
            .insert(
                {
                    "execution_id": event.execution_id,
                    "source_id": f"execution:{event.execution_id}",
                    "target_id": node_id,
                    "relation": event.event_type,
                    "metadata": {"timestamp": event.timestamp.isoformat()},
                }
            )
            .execute()
        )

    async def get_provenance_graph(self, execution_id: str) -> dict[str, Any]:
        """Return full graph for visualization / replay."""
        nodes = (
            await get_supabase_client().table("provenance_nodes").select("*").eq("execution_id", execution_id).execute()
        )

        edges = (
            await get_supabase_client().table("provenance_edges").select("*").eq("execution_id", execution_id).execute()
        )

        return {"nodes": nodes.data or [], "edges": edges.data or []}

    async def create_snapshot(self, execution_id: str) -> str:
        """Create a signed snapshot for audit/replay."""
        graph = await self.get_provenance_graph(execution_id)

        canonical = json.dumps(
            {"nodes": graph["nodes"], "edges": graph["edges"]},
            sort_keys=True,
        )

        snapshot = {
            "execution_id": execution_id,
            "nodes": graph["nodes"],
            "edges": graph["edges"],
            "integrity_hash": hashlib.sha256(canonical.encode()).hexdigest(),
        }

        result = await get_supabase_client().table("provenance_snapshots").insert(snapshot).execute()
        return result.data[0]["snapshot_id"]
