from __future__ import annotations

from backend.core.memory.fabric.semantic_memory import SemanticMemoryRecord
from backend.core.memory.stores.graph_store import GraphStore
from backend.core.memory.stores.vector_store import VectorStore


class MemoryFabric:
    def __init__(self):
        self.vector_store = VectorStore()
        self.graph_store = GraphStore()
        self.records: dict[str, SemanticMemoryRecord] = {}

    async def insert(self, record: SemanticMemoryRecord):
        self.records[record.memory_id] = record
        self.vector_store.insert(record, record.embedding)

    async def retrieve(
        self, tenant_id: str, query_embedding: list[float], top_k: int = 10, filters: dict | None = None
    ) -> list[SemanticMemoryRecord]:
        results = self.vector_store.search(query_embedding, limit=top_k)
        filtered = []
        for r in results:
            if r.tenant_id != tenant_id:
                continue
            if filters:
                match = True
                for k, v in filters.items():
                    if r.metadata.get(k) != v:
                        match = False
                        break
                if not match:
                    continue
            filtered.append(r)
        return filtered
