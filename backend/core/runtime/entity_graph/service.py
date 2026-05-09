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
            "edges": [e.model_dump() for e in edges],
            "total_nodes": len(self._nodes),
            "total_edges": len(self._edges),
        }
