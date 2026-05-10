# backend/core/runtime/entity_graph/pagerank.py
from __future__ import annotations

from typing import Any

import networkx as nx

from backend.core.runtime.entity_graph.service import EntityGraphService
from backend.core.services.observability_service import observability
from backend.core.tracing import trace_context


class GraphPageRank:
    """PageRank implementation for provenance and entity graphs."""

    @classmethod
    def rank(cls) -> GraphPageRank:
        return cls()

    async def compute(
        self,
        entity_id: str | None = None,
        max_nodes: int = 500,
        damping_factor: float = 0.85,
        iterations: int = 100,
        temporal_weight: bool = True,
    ) -> list[dict[str, Any]]:
        """Compute PageRank with temporal/provenance awareness."""
        with trace_context("pagerank.compute") as span:
            observability().increment("pagerank_computations_total")

            # 1. Get subgraph
            graph_data = await self._get_subgraph(entity_id, max_nodes)

            if not graph_data.get("nodes"):
                return []

            # 2. Build NetworkX graph
            g = nx.DiGraph()

            for node in graph_data["nodes"]:
                g.add_node(node["id"], **node)

            for edge in graph_data.get("edges", []):
                weight = edge.get("weight", 1.0)
                if temporal_weight and "timestamp" in edge:
                    # Recency bonus
                    weight *= 1.2
                g.add_edge(edge["source_id"], edge["target_id"], weight=weight)

            # 3. Run PageRank
            pagerank_scores = nx.pagerank(
                g,
                alpha=damping_factor,
                max_iter=iterations,
                tol=1e-6
            )

            # 4. Enrich results
            results = []
            for node_id, score in pagerank_scores.items():
                node_data = next((n for n in graph_data["nodes"] if n["id"] == node_id), {})
                results.append(
                    {
                        "node_id": node_id,
                        "entity_id": node_data.get("entity_id"),
                        "node_type": node_data.get("node_type"),
                        "pagerank_score": round(score, 6),
                        "label": f"{node_data.get('node_type', 'node')} • {node_data.get('entity_id', '')[:8]}",
                        "metadata": node_data.get("metadata", {}),
                    }
                )

            # Sort by influence
            results.sort(key=lambda x: x["pagerank_score"], reverse=True)

            observability().gauge("pagerank_max_score", max(r["pagerank_score"] for r in results))
            span.set_attribute("nodes_ranked", len(results))

            return results[:100]  # Top 100 most influential

    async def _get_subgraph(self, start_entity_id: str | None, max_nodes: int):
        """Fetch relevant subgraph for ranking."""
        if start_entity_id:
            return await EntityGraphService.graph().traverse_from(
                start_id=start_entity_id, relation_types=[], max_depth=4
            )
        else:
            # Global graph sample
            return await EntityGraphService.graph().get_world_state_graph()
