"""Domain-Aware RAG Router — classifies query then searches relevant indexes."""

from __future__ import annotations

import asyncio
import logging

from backend.runtime.rag.base_index import BaseIndex
from backend.runtime.rag.dataset_index import DatasetIndex
from backend.runtime.rag.document_index import DocumentIndex
from backend.runtime.rag.model_index import ModelIndex

log = logging.getLogger(__name__)


class RAGRouter:
    def __init__(self):
        self.indexes: dict[str, dict[str, BaseIndex]] = {
            "battery": {
                "document": DocumentIndex(domain="battery"),
                "model": ModelIndex(domain="battery"),
                "dataset": DatasetIndex(domain="battery"),
            },
            # Add more domains easily:
            # "grid": {...},
            # "flood": {...},
        }
        # Fallback for general queries, assuming 'general' domain indexes might exist or be handled differently
        self.indexes["general"] = {
            "document": DocumentIndex(domain="general"),
            "model": ModelIndex(domain="general"),
            "dataset": DatasetIndex(domain="general"),
        }

    def _classify_domain(self, query: str) -> str:
        """Simple but effective domain classifier."""
        q = query.lower()
        if any(kw in q for kw in ["lithium", "battery", "nmc", "plating", "cathode", "anode", "ev"]):
            return "battery"
        if any(kw in q for kw in ["grid", "power", "electricity", "transformer"]):
            return "grid"
        if any(kw in q for kw in ["flood", "fire", "climate", "weather"]):
            return "infrastructure"
        return "general"  # fallback

    async def retrieve(self, query: str, tenant_id: str = "public", top_k: int = 12) -> list[dict]:
        """Route to correct domain → search all three layers in parallel."""
        domain = self._classify_domain(query)
        indexes = self.indexes.get(domain, self.indexes["general"])  # Use "general" as default if domain not found

        tasks = []
        for _idx_type, index in indexes.items():
            tasks.append(index.search(query, tenant_id=tenant_id, limit=top_k // 3))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten + deduplicate
        combined = []
        seen = set()
        for batch in results:
            if isinstance(batch, Exception):
                log.warning("RAG layer failed in domain '%s': %s", domain, batch)
                continue
            for item in batch:
                key = item.get("id") or item.get("chunk_id") or item.get("hash")
                if key and key not in seen:
                    seen.add(key)
                    combined.append({**item, "domain": domain})

        log.info(f"RAGRouter: {len(combined)} items from domain '{domain}' (tenant={tenant_id})")
        return combined[:top_k]
