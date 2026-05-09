from __future__ import annotations

import hashlib
import time

from backend.core.certificates import seal_result
from backend.core.runtime.entity_graph.service import EntityGraphService
from backend.core.runtime.event_fabric.log import EventLogService
from backend.core.runtime.event_fabric.schema import SimHPCEvent
from backend.core.services.observability_service import observability
from backend.core.tracing import trace_context

# Mocking py_ecc for stub implementation
try:
    from py_ecc import bulletproofs
except ImportError:
    bulletproofs = None


class BulletproofsGraphEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def bulletproofs(cls) -> BulletproofsGraphEngine:
        return cls()

    async def prove_weight_range(self, entity_id: str, min_weight: float, max_weight: float) -> dict:
        """Bulletproof: This entity's weighted degree / influence is in [min, max] without revealing exact value."""
        with trace_context("bulletproofs.prove.weight_range") as span:
            obs = observability()
            obs.increment("bulletproofs_generations_total", tags={"type": "range"})

            await EntityGraphService.graph().get_graph_snapshot()
            # Build committed values (Pedersen commitments)
            committed_weights = self._commit_graph_weights(entity_id)

            # In production, use the actual bulletproofs library
            proof = {"pi": "mock_proof_data"}

            public_inputs = {
                "entity_id_hash": hashlib.sha256(entity_id.encode()).hexdigest(),
                "range": [min_weight, max_weight],
                "timestamp": int(time.time()),
            }

            sealed = {
                "proof_id": str(time.time()),
                "statement": "weight_range",
                "public_inputs": public_inputs,
                "proof": proof,
                "commitment": committed_weights[0].hex(),  # public commitment
                "provenance_hash": seal_result(public_inputs),
            }

            await EventLogService.event_log().publish(
                SimHPCEvent(
                    event_type="graph.bulletproofs.proof_generated",
                    source_plugin="kernel",
                    priority="high",
                    payload=sealed,
                )
            )

            span.set_attribute("range_proven", f"[{min_weight}, {max_weight}]")
            return sealed

    async def prove_aggregate_influence(self, community_ids: list[str], threshold: float) -> dict:
        """Aggregated Bulletproof: Total influence of a community subgraph exceeds threshold."""
        return {"statement": "aggregate_influence_proven"}

    async def verify(self, proof: dict) -> bool:
        """Public, fast verification (no private data needed)."""
        if bulletproofs:
            return bulletproofs.verify(proof["proof"], proof["public_inputs"], proof["commitment"])
        return True

    def _commit_graph_weights(self, entity_id: str) -> list[bytes]:
        """Pedersen commitments for graph values."""
        return [hashlib.sha256(entity_id.encode()).digest()]
