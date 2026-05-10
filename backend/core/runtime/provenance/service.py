from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.core.runtime.entity_graph.service import EntityGraphService
from backend.core.runtime.provenance.schema import ExecutionProvenanceGraph, ProvenanceEdge, ProvenanceNode
from backend.core.services.observability_service import observability
from backend.core.tracing import trace_context


class ExecutionProvenanceService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def provenance(cls) -> ExecutionProvenanceService:
        return cls()

    async def record_execution(self, run_id: str, context: dict[str, Any]) -> ExecutionProvenanceGraph:
        """Build and persist complete provenance graph for one execution run."""
        with trace_context("provenance.record_execution") as span:
            graph = ExecutionProvenanceGraph(run_id=run_id, root_node=run_id)

            # Root execution node
            exec_node = ProvenanceNode(
                node_type="execution_run", entity_id=run_id, metadata=context, timestamp=datetime.utcnow()
            )
            graph.nodes[exec_node.id] = exec_node

            # Hardware provenance
            if context.get("capacity_id"):
                hw_node = ProvenanceNode(
                    node_type="hardware_node", entity_id=context["capacity_id"], timestamp=datetime.utcnow()
                )
                graph.nodes[hw_node.id] = hw_node
                graph.edges.append(
                    ProvenanceEdge(
                        source_id=exec_node.id,
                        target_id=hw_node.id,
                        relation="SCHEDULED_ON",
                        metadata={"fractional": context.get("gpu_fraction", 1.0)},
                        timestamp=datetime.utcnow(),
                    )
                )

            # Forecast / Prediction
            if context.get("prediction"):
                pred_node = ProvenanceNode(
                    node_type="forecast", entity_id=context["prediction"].id, timestamp=datetime.utcnow()
                )
                graph.nodes[pred_node.id] = pred_node
                graph.edges.append(
                    ProvenanceEdge(
                        source_id=pred_node.id, target_id=exec_node.id, relation="PRODUCED", timestamp=datetime.utcnow()
                    )
                )

            # Agent actions
            for agent_id in context.get("agents_used", []):
                agent_node = ProvenanceNode(node_type="agent_action", entity_id=agent_id, timestamp=datetime.utcnow())
                graph.nodes[agent_node.id] = agent_node
                graph.edges.append(
                    ProvenanceEdge(
                        source_id=agent_node.id,
                        target_id=exec_node.id,
                        relation="CONTRIBUTED_TO",
                        timestamp=datetime.utcnow(),
                    )
                )

            # Store in unified Entity Graph
            await EntityGraphService.graph().ingest_provenance_graph(graph)

            observability().increment("provenance_graphs_created")
            span.set_attribute("node_count", len(graph.nodes))

            return graph

    async def get_provenance_trace(self, run_id: str, depth: int = 5) -> dict:
        """Retrieve full traceable provenance subgraph."""
        return await EntityGraphService.graph().traverse_from(
            start_id=run_id,
            relation_types=["SCHEDULED_ON", "PRODUCED", "CONTRIBUTED_TO", "RESOLVED_AS"],
            max_depth=depth,
        )
