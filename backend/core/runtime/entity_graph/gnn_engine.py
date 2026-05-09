from __future__ import annotations

import torch
from torch_geometric.data import Data

from backend.core.runtime.entity_graph.gnn import TemporalGNN
from backend.core.runtime.entity_graph.service import EntityGraphService
from backend.core.runtime.state_registry.service import StateRegistryService
from backend.core.services.observability_service import observability
from backend.core.tracing import trace_context


class GraphNeuralEngine:
    _instance = None
    _model: TemporalGNN | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model = TemporalGNN()
            cls._instance._model.eval()  # inference mode by default
        return cls._instance

    @classmethod
    def gnn(cls) -> GraphNeuralEngine:
        return cls()


async def compute_embeddings(self) -> dict[str, list[float]]:
    """Run GNN on current world state + entity graph."""
    with trace_context("gnn.compute_embeddings"):
        obs = observability()
        obs.increment("gnn_inference_total")

        state = await StateRegistryService.registry().get_current()
        # Assuming to_pyg_data exists on service
        graph_data: Data = await EntityGraphService.graph().to_pyg_data(state)

        with torch.no_grad():
            embeddings = self._model(
                graph_data.x,
                graph_data.edge_index,
                graph_data.edge_weight,
                state.regime,
            )

        # Map embeddings back to entity IDs
        node_map = await EntityGraphService.graph().get_node_id_map()
        result = {node_map[i]: emb.tolist() for i, emb in enumerate(embeddings)}

        obs.gauge("gnn_embedding_dim", float(embeddings.shape[1]))
        return result

    async def predict_link(self, source_id: str, target_id: str) -> float:
        """Temporal link prediction probability."""
        embeddings = await self.compute_embeddings()
        src_emb = torch.tensor(embeddings[source_id])
        tgt_emb = torch.tensor(embeddings[target_id])
        score = torch.sigmoid(torch.dot(src_emb, tgt_emb)).item()
        return float(score)
