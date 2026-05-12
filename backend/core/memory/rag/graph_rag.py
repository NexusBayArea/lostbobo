from __future__ import annotations

from typing import Any

from backend.core.memory.fabric.memory_fabric import MemoryFabric
from backend.core.memory.retrieval.retriever import Retriever
from backend.core.memory.stores.graph_store import GraphStore


class GraphRAG:
    def __init__(self, memory: MemoryFabric, retriever: Retriever, graph_store: GraphStore):
        self.memory = memory
        self.retriever = retriever
        self.graph_store = graph_store

    async def query(self, query: str, tenant_id: str, hop_depth: int = 2) -> dict[str, Any]:
        records = await self.retriever.retrieve(query, tenant_id, top_k=5)

        expanded_memory_ids = set()
        for r in records:
            neighbors = self.graph_store.get_neighbors(r.memory_id)
            expanded_memory_ids.update(neighbors)

        expanded_records = []
        for mid in expanded_memory_ids:
            rec = self.memory.records.get(mid)
            if rec is not None:
                expanded_records.append(rec)

        return {
            "primary": [r.text for r in records],
            "expanded": [r.text for r in expanded_records],
        }
