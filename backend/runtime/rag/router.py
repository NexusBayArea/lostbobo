"""Intelligent Multi-Layer RAG Router with tenant isolation."""

from __future__ import annotations

import asyncio
import logging
from typing import List, Dict, Any

from backend.runtime.rag.document_index import DocumentIndex
from backend.runtime.rag.structured_index import StructuredIndex
from backend.runtime.rag.experiment_index import ExperimentIndex

log = logging.getLogger(__name__)


class RAGRouter:
    def __init__(self):
        self.document = DocumentIndex()
        self.structured = StructuredIndex()
        self.experiment = ExperimentIndex()

    async def retrieve(
        self, 
        query: str, 
        tenant_id: str = "public", 
        top_k: int = 15
    ) -> List[Dict]:
        """Parallel retrieval across all three layers."""
        tasks = []

        # Layer 1: Always query documents
        tasks.append(self.document.search(query, tenant_id=tenant_id, limit=top_k//3))

        # Layer 2: Structured knowledge (parameters, constants)
        if any(kw in query.lower() for kw in ["parameter", "coeff", "rate", "value", "constant", "diffusion"]):
            tasks.append(self.structured.search(query, tenant_id=tenant_id, limit=top_k//3))

        # Layer 3: Experiment / simulation history
        if any(kw in query.lower() for kw in ["simulate", "run", "experiment", "previous", "result", "plating"]):
            tasks.append(self.experiment.search(query, tenant_id=tenant_id, limit=top_k//3))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten + deduplicate
        combined = []
        seen = set()
        for batch in results:
            if isinstance(batch, Exception):
                log.warning("Layer failed: %s", batch)
                continue
            for item in batch:
                key = item.get("id") or item.get("chunk_id") or item.get("hash")
                if key and key not in seen:
                    seen.add(key)
                    combined.append(item)

        log.info("RAGRouter retrieved %d items (tenant=%s)", len(combined), tenant_id)
        return combined[:top_k]
