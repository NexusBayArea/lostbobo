# backend/core/kernel/lineage/graph.py
from __future__ import annotations

from typing import Any

from backend.core.kernel.lineage.events import LineageEvent


class ProvenanceGraph:
    """Builds a traceable provenance graph from lineage events."""

    def __init__(self):
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: list[dict[str, Any]] = []

    async def build(self, execution_id: str) -> ProvenanceGraph:
        """Build graph from all events for an execution."""
        # In real code: fetch from Supabase
        events = await self._load_events(execution_id)

        for event in events:
            self._add_node(event)
            self._link_dependencies(event)

        return self

    async def _load_events(self, execution_id: str) -> list[LineageEvent]:
        # Placeholder for Supabase event loading
        return []

    def _add_node(self, event: LineageEvent):
        node_id = f"{event.source_type}:{event.source_id}"
        self.nodes[node_id] = {
            "id": node_id,
            "type": event.source_type,
            "name": event.source_id,
            "event_type": event.event_type,
            "payload": event.payload,
            "timestamp": event.timestamp,
        }

    def _link_dependencies(self, event: LineageEvent):
        # Link to execution root
        root_id = f"execution:{event.execution_id}"
        if root_id not in self.nodes:
            self.nodes[root_id] = {"id": root_id, "type": "execution", "name": event.execution_id}

        self.edges.append(
            {
                "source": root_id,
                "target": f"{event.source_type}:{event.source_id}",
                "relation": event.event_type,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {"nodes": list(self.nodes.values()), "edges": self.edges}
