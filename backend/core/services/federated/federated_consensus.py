import hashlib
from dataclasses import dataclass
from typing import Any

import numpy as np
import structlog

from backend.app.kernel.command_bus import command_bus
from backend.core.supabase_job_store import SupabaseJobStore
from backend.kernel.kernel import Kernel

log = structlog.get_logger(__name__)


@dataclass
class FederatedUpdate:
    node_id: str
    model_delta: dict[str, Any]
    local_reward: float
    trust_score: float
    novelty_contribution: float
    signature: str


class FederatedConsensusService:
    """Secure federated learning consensus with trust weighting."""

    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.supabase = SupabaseJobStore()

    async def aggregate(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Aggregate updates from multiple nodes with trust-weighted FedAvg."""
        job_id = payload["job_id"]
        updates_data = payload.get("updates", [])

        # Convert to objects
        updates = [FederatedUpdate(**u) for u in updates_data]

        if not updates:
            return {"success": False, "reason": "No updates received"}

        # Trust-weighted aggregation
        total_weight = 0.0
        aggregated_delta = None

        for update in updates:
            weight = float(update.trust_score * (1.0 + update.novelty_contribution))
            total_weight += weight

            if aggregated_delta is None:
                aggregated_delta = {k: np.array(v) * weight for k, v in update.model_delta.items()}
            else:
                for k in aggregated_delta:
                    aggregated_delta[k] += np.array(update.model_delta[k]) * weight

        # Normalize
        if total_weight > 0:
            for k in aggregated_delta:
                aggregated_delta[k] /= total_weight

        # Generate consensus signature
        delta_repr = str({k: v.tolist() for k, v in aggregated_delta.items()})
        consensus_signature = hashlib.sha256(delta_repr.encode()).hexdigest()

        # Store in Supabase
        await self.supabase.record_event(
            "federated_consensus_round",
            {
                "job_id": job_id,
                "node_count": len(updates),
                "total_weight": total_weight,
                "consensus_signature": consensus_signature,
                "aggregated_delta_hash": hashlib.sha256(delta_repr.encode()).hexdigest(),
            },
        )

        # Update global PPO policy via Kernel
        await command_bus.route(
            {
                "type": "RL_APPLY_FEDERATED_UPDATE",
                "payload": {
                    "delta": {k: v.tolist() for k, v in aggregated_delta.items()},
                    "consensus_signature": consensus_signature,
                    "job_id": job_id,
                },
            }
        )

        return {
            "success": True,
            "consensus_score": self._compute_consensus_quality(updates),
            "signature": consensus_signature,
            "nodes_participated": len(updates),
        }

    def _compute_consensus_quality(self, updates: list[FederatedUpdate]) -> float:
        trusts = [u.trust_score for u in updates]
        rewards = [u.local_reward for u in updates]
        return float(np.mean(trusts) * (1.0 - np.std(rewards) * 0.5))
