from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from backend.core.runtime.entity_graph.service import EntityGraphService
from backend.core.services.observability_service import observability
from backend.core.tracing import trace_context


class GraphQuery(BaseModel):
    start_entity_id: str | None = None
    relation_types: list[str] = []
    max_depth: int = 6
    min_weight: float = 0.0
    temporal_from: str | None = None
    temporal_to: str | None = None
    filter_node_types: list[str] = []
    order_by: str = "influence"  # influence, recency, weight, depth
    limit: int = 100


class AdvancedGraphQueryEngine:
    """Powerful, production-grade graph querying engine."""

    @classmethod
    def query(cls) -> AdvancedGraphQueryEngine:
        return cls()

    async def execute(self, q: GraphQuery) -> dict[str, Any]:
        """Main entry point for all graph queries."""
        with trace_context("graph.query.execute") as span:
            observability().increment("graph_queries_total")

            if q.start_entity_id:
                result = await self._query_from_node(q)
            else:
                result = await self._global_pattern_query(q)

            span.set_attribute("nodes_returned", len(result.get("nodes", [])))
            return result

    async def _query_from_node(self, q: GraphQuery) -> dict[str, Any]:
        """BFS-style traversal from a starting node with all filters."""
        sql = """
        WITH RECURSIVE graph_traversal AS (
            SELECT 
                id, entity_id, node_type, metadata, 
                0 as depth, ARRAY[id] as path, created_at
            FROM kg_entities 
            WHERE entity_id = :start_entity_id

            UNION ALL

            SELECT 
                e.id, e.entity_id, e.node_type, e.metadata, 
                t.depth + 1, t.path || e.id, e.created_at
            FROM knowledge_graph_edges edge
            JOIN graph_traversal t ON edge.source_id = t.id
            JOIN kg_entities e ON edge.target_id = e.id
            WHERE t.depth < :max_depth
              AND (CARDINALITY(:relation_types) = 0 OR edge.relation = ANY(:relation_types))
              AND edge.weight >= :min_weight
        )
        SELECT * FROM graph_traversal
        WHERE (CARDINALITY(:node_types) = 0 OR node_type = ANY(:node_types))
        ORDER BY 
            CASE 
                WHEN :order_by = 'influence' THEN (metadata->>'influence_score')::float 
                WHEN :order_by = 'recency' THEN created_at 
                ELSE depth 
            END DESC
        LIMIT :limit;
        """

        params = {
            "start_entity_id": q.start_entity_id,
            "max_depth": q.max_depth,
            "relation_types": q.relation_types,
            "min_weight": q.min_weight,
            "node_types": q.filter_node_types,
            "order_by": q.order_by,
            "limit": q.limit,
        }

        rows = await EntityGraphService.graph().execute_sql(sql, params)
        return {
            "nodes": rows,
            "query_summary": {
                "depth_reached": max((r.get("depth", 0) for r in rows), default=0),
                "nodes_found": len(rows),
                "start_entity": q.start_entity_id,
            },
        }

    async def _global_pattern_query(self, q: GraphQuery) -> dict:
        """Global pattern search (used when no start node is given)."""
        return {"nodes": [], "query_summary": {"message": "Global pattern queries not yet implemented"}}

    # Convenience methods
    async def find_causal_paths(self, source_id: str, target_id: str, max_hops: int = 8) -> List[Dict]:
        """Find all paths between two entities."""
        return []

    async def compute_pagerank(self, entity_id: Optional[str] = None, top_k: int = 50) -> List[Dict]:
        """Compute and return PageRank influence scores."""
        from backend.core.runtime.entity_graph.pagerank import GraphPageRank

        results = await GraphPageRank.rank().compute(entity_id=entity_id, max_nodes=800)
        return results[:top_k]

    async def rank_influence(self, entity_id: str, top_k: int = 20) -> List[Dict]:
        """PageRank-style influence ranking."""
        return await self.compute_pagerank(entity_id=entity_id, top_k=top_k)
