"""RAG Streaming — yields GraphRAG results progressively for real-time UI."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator

from backend.runtime.graphrag.graphrag_retriever import GraphRAGContext, GraphRAGRetriever

log = logging.getLogger(__name__)


class GraphRAGStreamer:
    def __init__(self):
        self.retriever = GraphRAGRetriever()

    async def stream_retrieve(
        self,
        question_id: str,
        query: str,
        category: str | None = None,
        hops: int | None = None,
        final_k: int | None = None,
    ) -> AsyncGenerator[dict, None]:
        """Yields progressive updates."""
        yield {"type": "start", "question_id": question_id, "query": query}

        try:
            embedding = await self.retriever._embed(query)
            seed_chunks = await self.retriever._vector_search(embedding, category)

            if seed_chunks:
                yield {
                    "type": "seed",
                    "chunks": seed_chunks[:5],
                    "total_seed": len(seed_chunks),
                }

            full_ctx: GraphRAGContext = await self.retriever.retrieve(
                question_id=question_id,
                query=query,
                category=category,
                hops=hops,
                final_k=final_k,
            )

            for i, chunk in enumerate(full_ctx.chunks):
                yield {
                    "type": "chunk",
                    "chunk": {
                        "id": chunk.chunk_id,
                        "text_preview": chunk.text[:280] + "..." if len(chunk.text) > 280 else chunk.text,
                        "score": round(chunk.final_score, 3),
                        "hop": chunk.hop_distance,
                    },
                    "progress": round((i + 1) / len(full_ctx.chunks) * 100, 1),
                }
                await asyncio.sleep(0.03)

            yield {
                "type": "complete",
                "context": {
                    "chunk_ids": full_ctx.chunk_ids,
                    "entity_ids": full_ctx.entity_ids,
                    "prompt_context": full_ctx.prompt_context,
                    "retrieval_ms": full_ctx.retrieval_ms,
                    "total_chunks": len(full_ctx.chunks),
                },
            }

        except Exception as exc:
            log.error("Streaming RAG failed: %s", exc)
            yield {"type": "error", "message": str(exc)}
