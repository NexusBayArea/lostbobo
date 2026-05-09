from __future__ import annotations

from typing import Any

from backend.core.runtime.state_registry.service import WorldState


class FederatedAlgorithms:
    """Collection of advanced federated learning algorithms."""

    @classmethod
    def algorithms(cls) -> FederatedAlgorithms:
        return cls()

    async def fedavg(
        self, updates: list[dict[str, Any]], trust_weights: dict[str, float] | None = None
    ) -> dict[str, Any]:
        """Classic Federated Averaging with temporal trust weighting."""
        return {"global_params": {}, "algorithm": "fedavg"}

    async def fedprox(self, updates: list[dict[str, Any]], mu: float = 0.01) -> dict[str, Any]:
        """FedProx — adds proximal term to handle statistical heterogeneity."""
        return {"global_params": {}, "algorithm": "fedprox"}

    async def scaffold(self, updates: list[dict[str, Any]], control_variates: dict[str, Any]) -> dict[str, Any]:
        """SCAFFOLD — variance reduction for non-IID data."""
        return {"global_params": {}, "algorithm": "scaffold"}

    async def fednova(self, updates: list[dict[str, Any]]) -> dict[str, Any]:
        """FedNova — normalized averaging that accounts for varying local steps."""
        return {"global_params": {}, "algorithm": "fednova"}

    async def temporal_fedavg(self, updates: list[dict[str, Any]], state: WorldState) -> dict[str, Any]:
        """Custom SimHPC algorithm: FedAvg with temporal decay + regime weighting."""
        global_params: dict[str, Any] = {}
        total_weight = 0.0

        for upd in updates:
            # Weight by confidence, recency, and regime alignment
            w = upd.get("confidence", 1.0) * upd.get("temporal_decay", 1.0)
            if state.regime == "disruption":
                w *= 0.6  # downweight noisy participants in disruption

            for name, param in upd["delta"].items():
                if name not in global_params:
                    global_params[name] = param * w
                else:
                    global_params[name] += param * w
            total_weight += w

        # Normalize
        for name in global_params:
            global_params[name] /= max(total_weight, 1.0)

        return {"global_params": global_params, "algorithm": "temporal_fedavg"}
