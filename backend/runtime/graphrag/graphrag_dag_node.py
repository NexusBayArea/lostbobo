"""GraphRAG DAG node."""

from __future__ import annotations

import logging
from typing import Any

from backend.runtime.graphrag.entity_extractor import EntityExtractor
from backend.runtime.graphrag.graphrag_retriever import GraphRAGContext, GraphRAGRetriever

log = logging.getLogger(__name__)


class GraphRAGDagNode:
    def __init__(self):
        self.retriever = GraphRAGRetriever()
        self.extractor = EntityExtractor(embed_entities=False)

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        question_id = context.get("question_id", "")
        query = context.get("query", "")
        category = context.get("category")
        hops = context.get("hops")
        final_k = context.get("final_k")
        run_extract = context.get("run_extractor", False)

        if run_extract:
            await self.extractor.process_unprocessed(limit=200)

        graph_ctx: GraphRAGContext = await self.retriever.retrieve(
            question_id=question_id,
            query=query,
            category=category,
            hops=hops,
            final_k=final_k,
        )

        return {
            "graph_context": graph_ctx,
            "chunk_ids": graph_ctx.chunk_ids,
            "prompt_context": graph_ctx.prompt_context,
            "entity_ids": graph_ctx.entity_ids,
            "edge_count": len(graph_ctx.edge_paths),
            "retrieval_ms": graph_ctx.retrieval_ms,
        }
