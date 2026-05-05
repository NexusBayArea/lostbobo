"""Vector RAG Agent — fast semantic search path."""

from __future__ import annotations

import logging

from backend.runtime.rag.router import RAGRouter

log = logging.getLogger(__name__)


class VectorRAGAgent:
    """Shallow but fast agent using pure vector similarity search."""

    def __init__(self) -> None:
        self._router = RAGRouter()

    async def run(self, query: str, tenant_id: str = "public") -> dict:
        try:
            context = await self._router.retrieve(query, tenant_id=tenant_id, top_k=8)
            top_text = context[0].get("text", "") if context else ""
            return {
                "content": f"Vector search: {top_text[:300]}{'...' if len(top_text) > 300 else ''}",
                "confidence": 0.72,
                "evidence": context[:3],
            }
        except Exception as exc:
            log.warning("VectorRAGAgent.run failed: %s", exc)
            return {"content": f"Vector agent error: {exc}", "confidence": 0.2, "evidence": []}
