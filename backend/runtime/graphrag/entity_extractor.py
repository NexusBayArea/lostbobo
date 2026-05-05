"""Entity + edge extractor for GraphRAG."""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass

from backend.app.core.supabase import get_supabase_client

log = logging.getLogger(__name__)

ENTITY_TYPES = ["PERSON", "ORG", "PRODUCT", "CONCEPT", "EVENT"]
MIN_TOKEN_LENGTH = 2
MAX_SINGLE_TOKEN_LENGTH = 50


@dataclass
class Entity:
    entity_id: str
    name: str
    label: str
    description: str | None
    source_chunk_ids: list[str]
    embedding: list[float] | None


@dataclass
class Edge:
    edge_id: str
    source_id: str
    target_id: str
    relation: str
    weight: float


async def _generate_embedding(text: str) -> list[float]:
    return [0.0] * 1536


class EntityExtractor:
    def __init__(self, embed_entities: bool = True):
        self.embed_entities = embed_entities
        self._sb = get_supabase_client()

    async def extract_from_chunk(self, chunk_id: str, text: str) -> tuple[list[Entity], list[Edge]]:
        entities = []
        edges = []

        words = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", text)
        seen_names = set()

        for name in words:
            if name in seen_names or len(name) < MIN_TOKEN_LENGTH:
                continue
            if len(name) > MAX_SINGLE_TOKEN_LENGTH:
                continue
            seen_names.add(name)

            entity_id = hashlib.sha256(name.lower().encode()).hexdigest()[:16]
            embedding = None
            if self.embed_entities:
                embedding = await _generate_embedding(name)

            entities.append(
                Entity(
                    entity_id=entity_id,
                    name=name,
                    label="CONCEPT",
                    description=None,
                    source_chunk_ids=[chunk_id],
                    embedding=embedding,
                )
            )

        return entities, edges

    async def process_unprocessed(self, limit: int = 200) -> dict:
        log.info("Entity extraction: processing up to %d chunks", limit)
        return {"entities_created": 0, "edges_created": 0}
