# backend/core/runtime/entity_graph/temporal_pagerank.py
from __future__ import annotations
from typing import Dict, List, Any
from datetime import datetime
import networkx as nx
import numpy as np

from backend.core.runtime.entity_graph.service import EntityGraphService
from backend.core.runtime.temporal.engine import TemporalEngine
from backend.core.services.observability_service import observability
from backend.core.tracing import trace_context


class TemporalPageRank:
    """Multiple temporal PageRank variants."""

    @classmethod
    def rank(cls) -> "TemporalPageRank":
        return cls()

    async def compute(
        self,
        variant: str = "decayed",   # decayed | windowed | streaming | regime_aware
        start_entity_id: str | None = None,
        time_window_days: int = 30,
        damping: float = 0.85,
        top_k: int = 50,
    ) -> List[Dict[str, Any]]:
        """Compute temporal PageRank with chosen variant."""
        with trace_context(f"temporal_pagerank.{variant}") as span:
            observability().increment(f"temporal_pagerank_{variant}_computations")

            graph_data = await self._get_temporal_subgraph(start_entity_id, time_window_days)

            if not graph_data.get("nodes"):
                return []

            g = self._build_temporal_graph(graph_data, variant)

            # Run standard PageRank on the weighted temporal graph
            scores = nx.pagerank(g, alpha=damping, max_iter=100)

            results = []
            for node_id, score in scores.items():
                node = next((n for n in graph_data["nodes"] if n["id"] == node_id), {})
                results.append({
                    "node_id": node_id,
                    "entity_id": node.get("entity_id"),
                    "node_type": node.get("node_type"),
                    "score": round(score, 6),
                    "label": f"{node.get('node_type', 'node')} • {node.get('entity_id', '')[:8]}",
                    "metadata": node.get("metadata", {})
                })

            results.sort(key=lambda x: x["score"], reverse=True)

            span.set_attribute("variant", variant)
            span.set_attribute("nodes_ranked", len(results))

            return results[:top_k]

    def _build_temporal_graph(self, graph_data: Dict[str, Any], variant: str) -> nx.DiGraph:
        g = nx.DiGraph()
        now = datetime.utcnow().timestamp()

        for node in graph_data["nodes"]:
            g.add_node(node["id"], **node)

        for edge in graph_data.get("edges", []):
            weight = edge.get("weight", 1.0)
            ts = edge.get("timestamp", now)

            if variant == "decayed":
                age_days = (now - ts) / 86400
                decay = np.exp(-0.05 * age_days)          # exponential decay
                weight *= decay

            elif variant == "windowed":
                age_days = (now - ts) / 86400
                weight *= 1.0 if age_days <= 14 else 0.3

            elif variant == "regime_aware":
                # Boost edges in high-volatility regimes
                regime = edge.get("metadata", {}).get("regime", "normal")
                weight *= 1.6 if regime in ("panic", "disruption") else 1.0

            g.add_edge(edge["source_id"], edge["target_id"], weight=weight)

        return g

    async def _get_temporal_subgraph(self, start_id: str | None, days: int):
        """Fetch time-bounded subgraph."""
        # This implementation requires get_temporal_subgraph to exist in EntityGraphService
        return await EntityGraphService.graph().get_temporal_subgraph(
            start_entity_id=start_id,
            days_back=days
        )
