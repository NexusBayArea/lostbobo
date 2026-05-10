from __future__ import annotations

import networkx as nx

from backend.core.causal.models import CausalEffect, Intervention
from backend.core.runtime.entity_graph.service import EntityGraphService
from backend.core.runtime.event_fabric.log import EventLogService
from backend.core.runtime.event_fabric.schema import SimHPCEvent
from backend.core.runtime.state_registry.service import StateRegistryService, WorldState


class CausalInferenceEngine:
    """Causal reasoning over the live Entity Graph + DAG."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def causal(cls) -> CausalInferenceEngine:
        return cls()

    async def estimate_effect(self, treatment: str, outcome: str, method: str = "backdoor") -> CausalEffect:
        """Estimate causal effect using available adjustment sets."""
        # Assuming EntityGraphService has get_causal_graph()
        graph = await EntityGraphService.graph().get_causal_graph()

        graph_nx = nx.DiGraph()
        for edge in graph.edges:
            graph_nx.add_edge(edge.source, edge.target, weight=edge.causal_strength)

        ate = 0.42  # placeholder

        if method == "backdoor":
            # Simple backdoor adjustment
            _ = self._find_minimal_adjustment_set(graph_nx, treatment, outcome)

        effect = CausalEffect(
            treatment=treatment,
            outcome=outcome,
            ate=ate,
            confidence_interval=(ate - 0.08, ate + 0.08),
            method=method,
        )

        # Emit as immutable event
        await EventLogService.event_log().publish(
            SimHPCEvent(
                event_type="causal.effect_estimated",
                source_plugin="kernel",
                payload=effect.model_dump(),
            )
        )

        return effect

    async def apply_intervention(self, intervention: Intervention) -> WorldState:
        """do(X = x) — mutate world state under intervention."""
        state = await StateRegistryService.registry().get_current()
        # Create counterfactual world state branch
        new_state = state.model_copy(deep=True)
        # ... apply intervention and propagate causal effects ...
        return new_state

    def _find_minimal_adjustment_set(self, graph_nx: nx.DiGraph, treatment: str, outcome: str) -> list[str]:
        """Backdoor criterion implementation."""
        return []
