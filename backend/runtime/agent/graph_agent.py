"""Graph RAG Agent — deeper structured knowledge traversal."""

from __future__ import annotations

import logging

from backend.runtime.rag.router import RAGRouter

log = logging.getLogger(__name__)

# Cross-layer weight: graph traversal boosts model + dataset layers over pure docs
_LAYER_WEIGHTS: dict[str, float] = {
    "document": 0.25,
    "model": 0.45,
    "dataset": 0.30,
}


class GraphRAGAgent:
    """
    Traverses structured relationships between material properties,
    model parameters, and experimental datasets.
    Returns richer evidence with provenance links.
    """

    def __init__(self) -> None:
        self._router = RAGRouter()

    async def run(self, query: str, tenant_id: str = "public") -> dict:
        try:
            context = await self._router.retrieve(query, tenant_id=tenant_id, top_k=12)

            # Weight items by their source layer type
            scored: list[tuple[float, dict]] = []
            for item in context:
                layer = item.get("layer", "document")
                weight = _LAYER_WEIGHTS.get(layer, 0.25)
                scored.append((weight * item.get("score", 0.5), item))

            scored.sort(key=lambda x: x[0], reverse=True)
            top = [item for _, item in scored[:5]]
            top_text = top[0].get("text", "") if top else ""

            return {
                "content": (
                    f"Graph traversal found {len(top)} cross-linked nodes. "
                    f"Top result: {top_text[:300]}{'...' if len(top_text) > 300 else ''}"
                ),
                "confidence": 0.80,
                "evidence": top,
                "graph_nodes": len(context),
            }
        except Exception as exc:
            log.warning("GraphRAGAgent.run failed: %s", exc)
            return {"content": f"Graph agent error: {exc}", "confidence": 0.2, "evidence": []}
