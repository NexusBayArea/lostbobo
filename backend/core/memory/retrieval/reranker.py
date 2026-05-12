from __future__ import annotations

from backend.core.memory.fabric.semantic_memory import SemanticMemoryRecord


class Reranker:
    async def rerank(
        self, query: str, candidates: list[SemanticMemoryRecord], top_n: int = 5
    ) -> list[SemanticMemoryRecord]:
        scored = [(c, c.confidence * 0.9 + hash(c.text) % 100 * 0.001) for c in candidates]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [c for c, _ in scored[:top_n]]
