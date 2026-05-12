from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from backend.core.memory.fabric.memory_fabric import MemoryFabric
from backend.core.memory.retrieval.compressor import ContextCompressor
from backend.core.memory.retrieval.reranker import Reranker
from backend.core.memory.retrieval.retriever import Retriever
from backend.core.trust.telemetry_hook import TrustTelemetry


class StreamingRAGOrchestrator:
    def __init__(
        self,
        memory: MemoryFabric,
        retriever: Retriever,
        reranker: Reranker,
        compressor: ContextCompressor,
        telemetry: TrustTelemetry,
    ):
        self.memory = memory
        self.retriever = retriever
        self.reranker = reranker
        self.compressor = compressor
        self.telemetry = telemetry

    async def query_stream(self, query: str, tenant_id: str, execution_id: str) -> AsyncGenerator[dict[str, Any], None]:
        await self.telemetry.report("rag.retrieval.started", execution_id, {"query": query})

        candidates = await self.retriever.retrieve(query, tenant_id, top_k=20)
        await self.telemetry.report("rag.retrieval.completed", execution_id, {"count": len(candidates)})
        yield {"stage": "retrieval", "count": len(candidates)}

        top_docs = await self.reranker.rerank(query, candidates, top_n=5)
        await self.telemetry.report("rag.rerank.completed", execution_id, {"top": len(top_docs)})
        yield {"stage": "rerank", "results": [r.text[:100] for r in top_docs]}

        context = await self.compressor.compress(top_docs, max_tokens=2048)
        await self.telemetry.report("rag.compression.completed", execution_id, {"length": len(context)})
        yield {"stage": "compression", "context_length": len(context)}

        await self.telemetry.report("rag.completed", execution_id, {})
        yield {"stage": "done", "context": context}
