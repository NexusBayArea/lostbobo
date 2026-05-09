import torch
import torch.nn.functional as functional
from torch_geometric.nn import GATConv, GCNConv


class TemporalGNN(torch.nn.Module):
    """Temporal-aware Graph Attention Network."""

    def __init__(self, hidden_dim: int = 128, heads: int = 4, dropout: float = 0.2):
        super().__init__()
        self.conv1 = GATConv(-1, hidden_dim, heads=heads, dropout=dropout)
        self.conv2 = GATConv(hidden_dim * heads, hidden_dim, heads=2, dropout=dropout)
        self.conv3 = GCNConv(hidden_dim * 2, hidden_dim)
        self.regime_embed = torch.nn.Embedding(4, 32)  # normal / panic / disruption / ...

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        edge_weight: torch.Tensor,
        regime: str,
    ) -> torch.Tensor:
        regime_idx = {"normal": 0, "panic": 1, "disruption": 2}.get(regime, 0)
        r_emb = self.regime_embed(torch.tensor([regime_idx], device=x.device))

        x = functional.elu(self.conv1(x, edge_index, edge_weight))
        x = functional.elu(self.conv2(x, edge_index, edge_weight))
        x = self.conv3(x, edge_index)

        # Inject regime embedding
        return x + r_emb
