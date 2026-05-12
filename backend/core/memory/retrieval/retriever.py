from __future__ import annotations

from backend.core.memory.fabric.memory_fabric import MemoryFabric
from backend.core.memory.fabric.semantic_memory import SemanticMemoryRecord
from backend.core.memory.retrieval.embeddings import EmbeddingService


class Retriever:
    def __init__(self, memory: MemoryFabric, embedder: EmbeddingService):
        self.memory = memory
        self.embedder = embedder

    async def retrieve(
        self,
        query: str,
        tenant_id: str,
        top_k: int = 10,
        filters: dict | None = None,
    ) -> list[SemanticMemoryRecord]:
        query_emb = (await self.embedder.embed([query]))[0]
        records = await self.memory.retrieve(tenant_id, query_emb, top_k=top_k, filters=filters)
        return records
