"""
backend/core/embedding/service.py
─────────────────────────────────
Canonical embedding pipeline with retry + dead-letter queue.
"""

from __future__ import annotations

import asyncio
import logging

from openai import AsyncOpenAI

from backend.app.core.supabase import get_supabase_client
from backend.core.secrets import require_secret

log = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=require_secret("OPENAI_API_KEY"))


class EmbeddingService:
    MAX_RETRIES = 5
    BASE_BACKOFF = 2.0

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=texts,
            dimensions=1536,
        )
        return [data.embedding for data in response.data]

    async def process_unembedded_chunks(self, batch_size: int = 80) -> int:
        """Process unembedded chunks with retry + dead-letter."""
        sb = get_supabase_client()
        if not sb:
            log.error("Supabase client unavailable")
            return 0

        # Find unembedded chunks
        resp = sb.table("document_chunks").select("id, content").is_("embedding", None).limit(batch_size * 2).execute()

        chunks = resp.data or []
        if not chunks:
            return 0

        processed = 0
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [c["content"] for c in batch]
            chunk_ids = [c["id"] for c in batch]

            for attempt in range(self.MAX_RETRIES):
                try:
                    embeddings = await self.embed_batch(texts)

                    updates = [{"id": cid, "embedding": emb} for cid, emb in zip(chunk_ids, embeddings, strict=True)]

                    sb.table("document_chunks").upsert(updates, on_conflict="id").execute()
                    processed += len(batch)
                    break

                except Exception as e:
                    if attempt == self.MAX_RETRIES - 1:
                        # Move to dead-letter
                        dead_letters = [
                            {
                                "chunk_id": cid,
                                "content": txt,
                                "error_message": str(e),
                                "retry_count": self.MAX_RETRIES,
                            }
                            for cid, txt in zip(chunk_ids, texts, strict=True)
                        ]

                        sb.table("document_chunks_dead_letter").insert(dead_letters).execute()
                        log.error("Chunk batch moved to dead-letter after %s failures", self.MAX_RETRIES)
                    else:
                        backoff = self.BASE_BACKOFF**attempt
                        log.warning("Embedding attempt %s failed, retrying in %ss", attempt + 1, backoff)
                        await asyncio.sleep(backoff)

        log.info("Embedding job completed — %s chunks processed", processed)
        return processed


embedding_service = EmbeddingService()
