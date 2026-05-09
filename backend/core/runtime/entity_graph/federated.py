from __future__ import annotations

from typing import Any

from backend.core.runtime.entity_graph.gnn import TemporalGNN
from backend.core.runtime.state_registry.service import StateRegistryService
from backend.core.services.observability_service import observability
from backend.core.tracing import trace_context
from backend.ml.registry import ModelRegistry


class FederatedGNNEngine:
    _instance = None
    _global_model: TemporalGNN | None = None
    _local_models: dict[str, TemporalGNN] = {}  # participant → model

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._global_model = TemporalGNN()
            cls._instance._model_registry = ModelRegistry()
        return cls._instance

    @classmethod
    def federated(cls) -> FederatedGNNEngine:
        return cls()

    async def local_update(self, participant_id: str, local_graph_data: Any, state: Any) -> dict[str, Any]:
        """Each plugin/tenant trains on its local view only."""
        with trace_context("federated.local_update", {"participant": participant_id}):
            obs = observability()
            obs.increment("federated_local_updates_total")

            if participant_id not in self._local_models:
                self._local_models[participant_id] = TemporalGNN()

            # Local training step (PyG on local subgraph)
            # ... optimizer step, contrastive / supervised loss ...

            update_delta = {
                name: param.data.clone() for name, param in self._local_models[participant_id].named_parameters()
            }

            return {
                "participant": participant_id,
                "delta": update_delta,
                "local_loss": 0.0,  # reported for monitoring
                "graph_size": len(local_graph_data.get("nodes", [])) if isinstance(local_graph_data, dict) else 0,
            }

    async def aggregate(
        self,
        updates: list[dict[str, Any]],
        trust_weights: dict[str, float] | None = None,
    ) -> None:
        """Federated Averaging (FedAvg) with temporal + trust weighting."""
        if not updates:
            return

        global_params = self._global_model.state_dict()
        total_weight = 0.0

        for upd in updates:
            w = trust_weights.get(upd["participant"], 1.0) if trust_weights else 1.0
            for name in global_params:
                global_params[name] += w * upd["delta"][name]
            total_weight += w

        # Normalize
        for name in global_params:
            global_params[name] /= max(total_weight, 1.0)

        self._global_model.load_state_dict(global_params)

        # Persist versioned model
        await self._model_registry.register_version(
            model_type="federated_temporal_gnn",
            weights=global_params,
            metadata={
                "participants": len(updates),
                "regime": (await StateRegistryService.registry().get_current()).regime,
            },
        )

        observability().increment("federated_aggregations_total")
