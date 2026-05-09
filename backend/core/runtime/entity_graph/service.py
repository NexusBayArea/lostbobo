"""Entity graph service — kernel-mediated graph mutations with state registry integration."""

from __future__ import annotations

import logging
from typing import Any

from backend.app.core.supabase import get_supabase_client
from backend.core.runtime.entity_graph.schema import EntityNode, RelationshipEdge
from backend.core.runtime.event_fabric.schema import SimHPCEvent
from backend.core.runtime.state_registry.service import StateRegistryService

log = logging.getLogger(__name__)


class EntityGraphService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._supabase = get_supabase_client()
            cls._instance._nodes: dict[str, EntityNode] = {}
            cls._instance._edges: list[RelationshipEdge] = []
        return cls._instance

    @classmethod
    def graph(cls) -> EntityGraphService:
        return cls()

    async def add_node(self, node: EntityNode) -> None:
        self._nodes[node.entity_id] = node
        if self._supabase:
            try:
                self._supabase.table("knowledge_graph_nodes").upsert(node.model_dump()).execute()
            except Exception as exc:
                log.warning("Failed to persist entity node: %s", exc)

    async def add_edge(self, edge: RelationshipEdge, event: SimHPCEvent) -> None:
        if self._supabase:
            try:
                self._supabase.table("knowledge_graph_edges").insert(edge.model_dump()).execute()
            except Exception as exc:
                log.warning("Failed to persist edge: %s", exc)

        await StateRegistryService.registry().mutate(event)

    async def traverse(
        self,
        start_id: str,
        max_hops: int = 3,
        relation_filter: str | None = None,
    ) -> list[EntityNode]:
        if not self._supabase:
            return list(self._nodes.values())[: max_hops * 5]

        try:
            params = {"start_id": start_id, "max_hops": max_hops}
            resp = self._supabase.rpc("get_entity_neighbours", params).execute()
            return [EntityNode.model_validate(r) for r in (resp.data or [])]
        except Exception as exc:
            log.warning("Graph traversal failed: %s", exc)
            return []

    async def get_graph_snapshot(self, max_nodes: int = 200) -> dict[str, Any]:
        nodes = list(self._nodes.values())[:max_nodes]
        edges = self._edges[: max_nodes * 2]
        return {
            "nodes": [n.model_dump() for n in nodes],
            "nodes_map": {n.entity_id: n.model_dump() for n in nodes},
            "edges": [e.model_dump() for e in edges],
            "total_nodes": len(self._nodes),
            "total_edges": len(self._edges),
        }

    async def get_world_state_graph(self) -> dict[str, Any]:
        """Unified view: merges live WorldState + temporal Entity Graph."""
        import time

        from backend.core.services.observability_service import observability
        from backend.core.tracing import trace_context

        with trace_context("core_graph.world_state") as span:
            obs = observability()
            obs.increment("core_graph_requests_total")

            state = await StateRegistryService.registry().get_current()
            graph = await self.get_graph_snapshot(max_nodes=500)

            # Merge WorldState entities into graph nodes
            for key, ent in state.entities.items():
                if key in graph["nodes_map"]:
                    node = graph["nodes_map"][key]
                    node.update(
                        {
                            "value": ent.value,
                            "uncertainty": ent.uncertainty,
                            "last_updated": ent.last_updated,
                            "regime": state.regime,
                        }
                    )

            result = {
                "nodes": list(graph["nodes_map"].values()),
                "edges": graph["edges"],
                "state": {
                    "timestamp": state.timestamp,
                    "regime": state.regime,
                    "entropy": sum(e.uncertainty for e in state.entities.values()),
                    "total_entities": len(state.entities),
                },
                "generated_at": time.time(),
            }

            span.set_attribute("node_count", len(result["nodes"]))
            return result

    async def core_graph_snapshot(self) -> dict[str, Any]:
        """Minimal high-performance snapshot optimized for UI consumption."""
        return await self.get_world_state_graph()
