"""Multi-Layer RAG Router with smart parallel retrieval."""

from __future__ import annotations

import asyncio
import logging

from backend.runtime.rag.document_index import DocumentIndex
from backend.runtime.rag.experiment_index import ExperimentIndex
from backend.runtime.rag.structured_index import StructuredIndex

log = logging.getLogger(__name__)


class RAGRouter:
    def __init__(self):
        self.document = DocumentIndex()
        self.structured = StructuredIndex()
        self.experiment = ExperimentIndex()

    async def retrieve(self, query: str, tenant_id: str = "public", top_k: int = 15) -> list[dict]:
        """Parallel retrieval from all three layers."""
        tasks = []

        # Layer 1: Documents (always)
        tasks.append(self.document.search(query, tenant_id=tenant_id, limit=top_k // 3))

        # Layer 2: Structured (parameters, constants)
        if any(
            kw in query.lower()
            for kw in ["parameter", "coeff", "rate", "value", "constant", "diffusion", "conductivity"]
        ):
            tasks.append(self.structured.search(query, tenant_id=tenant_id, limit=top_k // 3))

        # Layer 3: Experiments / simulations
        if any(
            kw in query.lower() for kw in ["simulate", "run", "experiment", "previous", "result", "plating", "charge"]
        ):
            tasks.append(self.experiment.search(query, tenant_id=tenant_id, limit=top_k // 3))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten + deduplicate
        combined = []
        seen = set()
        for batch in results:
            if isinstance(batch, Exception):
                log.warning("RAG layer failed: %s", batch)
                continue
            for item in batch:
                key = item.get("id") or item.get("chunk_id") or item.get("hash")
                if key and key not in seen:
                    seen.add(key)
                    combined.append(item)

        log.info("RAGRouter: %d items retrieved (tenant=%s)", len(combined), tenant_id)
        return combined[:top_k]
