from __future__ import annotations

import time
import uuid
from typing import Any

from backend.core.memory.fabric.memory_fabric import MemoryFabric
from backend.core.memory.fabric.semantic_memory import SemanticMemoryRecord
from backend.core.memory.retrieval.embeddings import EmbeddingService


class IngestionPipeline:
    def __init__(self, memory: MemoryFabric, embedder: EmbeddingService):
        self.memory = memory
        self.embedder = embedder

    async def ingest(
        self,
        documents: list[dict[str, Any]],
        plugin_name: str = "kernel",
        tenant_id: str = "default",
    ) -> int:
        chunks = []
        for doc in documents:
            chunk_id = str(uuid.uuid4())
            chunks.append(
                {
                    "id": chunk_id,
                    "text": doc.get("content", ""),
                    "metadata": doc.get("metadata", {}),
                }
            )

        texts = [c["text"] for c in chunks]
        embeddings = await self.embedder.embed(texts)

        for i, chunk in enumerate(chunks):
            record = SemanticMemoryRecord(
                memory_id=chunk["id"],
                tenant_id=tenant_id,
                plugin_name=plugin_name,
                timestamp=time.time(),
                confidence=1.0,
                text=chunk["text"],
                embedding=embeddings[i],
                concepts=[],
                metadata=chunk["metadata"],
            )
            await self.memory.insert(record)

        return len(chunks)
