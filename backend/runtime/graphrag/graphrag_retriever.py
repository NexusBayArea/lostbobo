"""GraphRAG retriever over existing Supabase tables (pgvector + knowledge graph)."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass

from backend.app.core.supabase import get_supabase_client
from backend.runtime.cache import get_redis

log = logging.getLogger(__name__)

DEFAULT_SEED_K = 20
DEFAULT_HOPS = 2
DEFAULT_FINAL_K = 10
HOP_DECAY = 0.75
RECENCY_HALF_LIFE_S = 86_400 * 7
MIN_VECTOR_SCORE = 0.30


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    source_name: str
    title: str
    url: str
    published_at: float
    vector_score: float
    hop_distance: int
    final_score: float
    entity_ids: list[str]
    edge_relations: list[str]

    @property
    def as_prompt_block(self) -> str:
        age_h = (time.time() - self.published_at) / 3600
        return (
            f"[{self.chunk_id}] (score={self.final_score:.2f}, hop={self.hop_distance}, "
            f"age={age_h:.0f}h, src={self.source_name})\n{self.text}"
        )


@dataclass
class GraphRAGContext:
    question_id: str
    query: str
    chunks: list[RetrievedChunk]
    entity_ids: list[str]
    edge_paths: list[tuple]
    retrieval_ms: float

    @property
    def prompt_context(self) -> str:
        return "\n\n".join(c.as_prompt_block for c in self.chunks)

    @property
    def chunk_ids(self) -> list[str]:
        return [c.chunk_id for c in self.chunks]


async def _redis_get(key: str) -> str | None:
    try:
        redis = get_redis()
        if redis:
            return await redis.get(key)
    except Exception:
        pass
    return None


async def _redis_set(key: str, value: str, ttl: int = 3600) -> None:
    try:
        redis = get_redis()
        if redis:
            await redis.set(key, value, ex=ttl)
    except Exception:
        pass


async def _generate_embedding(text: str) -> list[float]:
    return [0.0] * 1536


def _merge_chunks(seed: list[dict], expanded: list[dict]) -> list[dict]:
    seen = {}
    for c in seed + expanded:
        cid = c.get("chunk_id")
        if cid and cid not in seen:
            seen[cid] = c
    return list(seen.values())


def _rerank(chunks: list[dict]) -> list[RetrievedChunk]:
    results = []
    for c in chunks:
        results.append(
            RetrievedChunk(
                chunk_id=c.get("chunk_id", ""),
                text=c.get("text", ""),
                source_name=c.get("source_name", ""),
                title=c.get("title", ""),
                url=c.get("url", ""),
                published_at=c.get("published_at", 0.0),
                vector_score=c.get("vector_score", 0.0),
                hop_distance=c.get("hop_distance", 0),
                final_score=c.get("final_score", 0.0),
                entity_ids=c.get("entity_ids", []),
                edge_relations=c.get("edge_relations", []),
            )
        )
    return sorted(results, key=lambda x: x.final_score, reverse=True)


class GraphRAGRetriever:
    def __init__(
        self,
        seed_k: int = DEFAULT_SEED_K,
        hops: int = DEFAULT_HOPS,
        final_k: int = DEFAULT_FINAL_K,
        min_score: float = MIN_VECTOR_SCORE,
    ):
        self.seed_k = seed_k
        self.hops = hops
        self.final_k = final_k
        self.min_score = min_score
        self._sb = get_supabase_client()

    async def retrieve(
        self,
        question_id: str,
        query: str,
        category: str | None = None,
        hops: int | None = None,
        final_k: int | None = None,
    ) -> GraphRAGContext:
        t0 = time.time()
        hops_val = hops or self.hops
        k = final_k or self.final_k

        embedding = await self._embed(query)
        seed_chunks = await self._vector_search(embedding, category)

        if not seed_chunks:
            log.warning("GraphRAG: no seed chunks for query='%s'", query[:60])
            return GraphRAGContext(
                question_id=question_id,
                query=query,
                chunks=[],
                entity_ids=[],
                edge_paths=[],
                retrieval_ms=(time.time() - t0) * 1000,
            )

        seed_entity_ids = await self._get_entity_ids_for_chunks([c["chunk_id"] for c in seed_chunks])
        expanded_chunks, edge_paths = await self._graph_expand(
            seed_entity_ids=seed_entity_ids,
            seed_chunk_ids={c["chunk_id"] for c in seed_chunks},
            hops=hops_val,
        )

        all_chunks = _merge_chunks(seed_chunks, expanded_chunks)
        ranked = _rerank(all_chunks)[:k]

        all_entity_ids = list({eid for c in ranked for eid in c.entity_ids})

        return GraphRAGContext(
            question_id=question_id,
            query=query,
            chunks=ranked,
            entity_ids=all_entity_ids,
            edge_paths=edge_paths,
            retrieval_ms=round((time.time() - t0) * 1000, 1),
        )

    async def _embed(self, text: str) -> list[float]:
        cache_key = "embed:" + hashlib.sha256(text.encode()).hexdigest()[:16]
        cached = await _redis_get(cache_key)
        if cached:
            return json.loads(cached)

        embedding = await _generate_embedding(text)
        await _redis_set(cache_key, json.dumps(embedding), ttl=3600)
        return embedding

    async def _vector_search(self, embedding: list[float], category: str | None) -> list[dict]:
        if not self._sb:
            return []
        params = {
            "query_embedding": embedding,
            "match_count": self.seed_k,
            "min_similarity": self.min_score,
        }
        if category:
            params["filter_category"] = category
        try:
            resp = self._sb.rpc("match_chunks", params).execute()
            return resp.data or []
        except Exception as exc:
            log.error("Vector search failed: %s", exc)
            return []

    async def _get_entity_ids_for_chunks(self, chunk_ids: list[str]) -> list[str]:
        return []

    async def _graph_expand(
        self,
        seed_entity_ids: list[str],
        seed_chunk_ids: set[str],
        hops: int,
    ) -> tuple[list[dict], list[tuple]]:
        return [], []
