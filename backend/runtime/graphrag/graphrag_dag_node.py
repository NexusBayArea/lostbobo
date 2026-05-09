"""GraphRAG DAG node — integrates cleanly with your existing runtime DAG."""

from __future__ import annotations

import logging
from typing import Any

from backend.core.kernel.command_bus import command_bus
from backend.core.services.tracing import tracer
from backend.runtime.graphrag.graphrag_retriever import GraphRAGContext, GraphRAGRetriever

log = logging.getLogger(__name__)


class GraphRAGDagNode:
    def __init__(self):
        self.retriever = GraphRAGRetriever()

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        question_id = context.get("question_id", "")
        query = context.get("query", "")

        if not question_id or not query:
            return {"graph_context": None, "chunk_ids": [], "prompt_context": "(no context)"}

        with tracer.start_as_current_span(
            "graphrag.dag_node",
            attributes={"question_id": question_id},
        ):
            graph_ctx: GraphRAGContext = await self.retriever.retrieve(
                question_id=question_id,
                query=query,
                category=context.get("category"),
                hops=context.get("hops"),
                final_k=context.get("final_k"),
            )

            return {
                "graph_context": graph_ctx,
                "chunk_ids": graph_ctx.chunk_ids,
                "prompt_context": graph_ctx.prompt_context,
                "entity_ids": graph_ctx.entity_ids,
                "edge_count": len(graph_ctx.edge_paths),
                "retrieval_ms": graph_ctx.retrieval_ms,
            }


@command_bus.handler("GRAPHRAG_RETRIEVE")
async def handle_graphrag_retrieve(kernel, payload: dict) -> dict[str, Any]:
    node = GraphRAGDagNode()
    return await node.run(payload)
