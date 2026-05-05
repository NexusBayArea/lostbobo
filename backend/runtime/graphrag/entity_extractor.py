"""Entity & edge extractor for GraphRAG — builds the knowledge graph."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from backend.app.core.supabase import get_supabase_client

log = logging.getLogger(__name__)


@dataclass
class ExtractedEntity:
    entity_id: str
    entity_type: str
    name: str
    source_text: str
    chunk_id: str


@dataclass
class ExtractedEdge:
    source_id: str
    target_id: str
    relation: str
    weight: float
    evidence_id: str


class EntityExtractor:
    def __init__(self):
        self._sb = get_supabase_client()

    async def process_unprocessed(self, limit: int = 200) -> tuple[int, int]:
        """Placeholder — expand when you have real ingestion pipeline."""
        log.info("EntityExtractor: processing up to %d unprocessed chunks", limit)
        return 0, 0


def _normalise_name(name: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", name.lower())).strip()
