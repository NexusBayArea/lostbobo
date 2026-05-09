"""GraphRAG Plugin — wraps existing GraphRAG retriever as a domain plugin."""

from __future__ import annotations

from typing import Any

from backend.plugins.base import PluginBase
from backend.plugins.registry import PluginRegistry


@PluginRegistry.register("graphrag")
class GraphRAGPlugin(PluginBase):
    name = "graphrag"
    version = "0.1.0"
    category = "retrieval"
    description = "GraphRAG retrieval with pgvector embeddings, knowledge graph expansion, and conformal calibration"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        from backend.runtime.graphrag.graphrag_dag_node import GraphRAGDagNode

        node = GraphRAGDagNode()
        return await node.run(input_data)

    async def validate_input(self, input_data: dict[str, Any]) -> bool:
        return bool(input_data.get("question_id") and input_data.get("query"))
