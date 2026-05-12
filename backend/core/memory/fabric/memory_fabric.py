from __future__ import annotations

from backend.core.memory.fabric.memory_types import BaseMemoryRecord
from backend.core.memory.stores.graph_store import GraphStore
from backend.core.memory.stores.vector_store import VectorStore


class MemoryFabric:
    def __init__(self):
        self.vector_store = VectorStore()
        self.graph_store = GraphStore()
        self.records: dict[str, BaseMemoryRecord] = {}

    async def insert(self, record: BaseMemoryRecord):
        self.records[record.memory_id] = record
        if hasattr(record, "embedding") and record.embedding:
            self.vector_store.insert(record, record.embedding)

    async def retrieve(
        self, tenant_id: str, query_embedding: list[float], top_k: int = 10, filters: dict | None = None
    ) -> list[BaseMemoryRecord]:
        results = self.vector_store.search(query_embedding, limit=top_k)
        filtered = []
        for r in results:
            if r.tenant_id != tenant_id:
                continue
            if filters:
                match = True
                for k, v in filters.items():
                    if k == "plugin_name":
                        if getattr(r, "plugin_name", None) != v:
                            match = False
                    elif r.metadata.get(k) != v:
                        match = False
                    if not match:
                        break
                if not match:
                    continue
            filtered.append(r)
        return filtered

    async def retrieve_by_type(
        self,
        tenant_id: str,
        memory_type: str | None = None,
        filter_dict: dict | None = None,
    ) -> list[BaseMemoryRecord]:
        results = []
        for rec in self.records.values():
            if rec.tenant_id != tenant_id:
                continue
            if memory_type and rec.memory_type.value != memory_type:
                continue
            if filter_dict:
                match = True
                for k, v in filter_dict.items():
                    if k == "plugin_name":
                        if getattr(rec, "plugin_name", None) != v:
                            match = False
                    elif k.startswith("metadata."):
                        meta_key = k[9:]
                        if rec.metadata.get(meta_key) != v:
                            match = False
                    elif k.startswith("execution_state."):
                        state_key = k[16:]
                        state_val = (
                            getattr(rec, "execution_state", {}).get(state_key)
                            if hasattr(rec, "execution_state")
                            else None
                        )
                        if state_val != v:
                            match = False
                    elif rec.metadata.get(k) != v:
                        match = False
                    if not match:
                        break
                if not match:
                    continue
            results.append(rec)
        return results

    async def retrieve_by_id(self, memory_id: str) -> BaseMemoryRecord | None:
        return self.records.get(memory_id)
