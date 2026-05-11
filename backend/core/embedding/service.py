"""
backend/core/embedding/service.py
─────────────────────────────────
Canonical embedding pipeline using OpenAI text-embedding-3-small (1536 dim).
Batched, retryable, idempotent, and integrated with Flywheel.
"""

from __future__ import annotations

import logging

from openai import AsyncOpenAI

from backend.app.core.supabase import get_supabase_client
from backend.core.secrets import require_secret

log = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=require_secret("OPENAI_API_KEY"))


class EmbeddingService:
    """Singleton embedding service."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        if not texts:
            return []

        response = await client.embeddings.create(model="text-embedding-3-small", input=texts, dimensions=1536)
        return [data.embedding for data in response.data]

    async def process_unembedded_chunks(self, batch_size: int = 100) -> int:
        """Find and embed all chunks where embedding IS NULL."""
        sb = get_supabase_client()
        if not sb:
            log.error("Supabase client not available")
            return 0

        # Find unembedded chunks
        resp = sb.table("document_chunks").select("id, content").is_("embedding", None).limit(batch_size * 2).execute()

        chunks = resp.data or []
        if not chunks:
            log.debug("No unembedded chunks found")
            return 0

        log.info("Found %d unembedded chunks — starting embedding", len(chunks))

        processed = 0
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [c["content"] for c in batch]
            chunk_ids = [c["id"] for c in batch]

            try:
                embeddings = await self.embed_batch(texts)

                # Update in Supabase
                updates = [{"id": cid, "embedding": emb} for cid, emb in zip(chunk_ids, embeddings, strict=True)]

                sb.table("document_chunks").upsert(updates, on_conflict="id").execute()
                processed += len(batch)

                log.info("Embedded batch %d — %d/%d chunks", i // batch_size + 1, processed, len(chunks))

            except Exception as e:
                log.error("Embedding batch failed: %s", e)

        log.info("Embedding pipeline completed — %d chunks embedded", processed)
        return processed


embedding_service = EmbeddingService()
