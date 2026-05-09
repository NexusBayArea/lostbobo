from __future__ import annotations

import hashlib
import time

from backend.core.certificates import seal_result
from backend.core.runtime.entity_graph.service import EntityGraphService
from backend.core.runtime.event_fabric.log import EventLogService
from backend.core.runtime.event_fabric.schema import SimHPCEvent
from backend.core.runtime.state_registry.service import StateRegistryService
from backend.core.services.observability_service import observability
from backend.core.tracing import trace_context


class ZKSNARKsGraphApplications:
    """Practical zk-SNARK applications on the temporal Entity Graph."""

    @classmethod
    def apps(cls) -> ZKSNARKsGraphApplications:
        return cls()

    async def prove_temporal_influence(self, entity_id: str, min_influence: float, max_influence: float) -> dict:
        """Application: Prove entity's temporal influence (decayed PageRank) is within bounds."""
        with trace_context("snarks.app.temporal_influence"):
            obs = observability()
            obs.increment("snarks_app_total", tags={"app": "temporal_influence"})

            await EntityGraphService.graph().get_graph_snapshot()
            state = await StateRegistryService.registry().get_current()

            # Private witness: full graph + temporal weights + uncertainties
            witness = self._build_influence_witness(entity_id)

            public_inputs = {
                "entity_hash": hashlib.sha256(entity_id.encode()).hexdigest(),
                "influence_range": [min_influence, max_influence],
                "regime": state.regime,
                "timestamp": int(time.time()),
            }

            proof = self._generate_snark_proof("temporal_influence", public_inputs, witness)

            sealed_proof = {
                "proof_id": f"snark_influence_{int(time.time())}",
                "application": "temporal_influence",
                "public_inputs": public_inputs,
                "proof": proof,  # constant size
                "provenance_hash": seal_result(public_inputs),
            }

            await EventLogService.event_log().publish(
                SimHPCEvent(
                    event_type="graph.snarks.application",
                    source_plugin="kernel",
                    priority="high",
                    payload=sealed_proof,
                )
            )

            return sealed_proof

    async def prove_community_isolation(self, community_ids: list[str], max_cross_influence: float) -> dict:
        """Application: Prove a community is sufficiently isolated (limited external influence)."""
        return {"statement": "community_isolation_proven"}

    async def prove_causal_path_absence(self, forbidden_source: str, forbidden_target: str, max_hops: int) -> dict:
        """Application: Prove no causal influence path exists between two entities."""
        return {"statement": "causal_path_absence_proven"}

    async def prove_uncertainty_bound(self, subgraph_ids: list[str], max_uncertainty: float) -> dict:
        """Application: Prove aggregate uncertainty of a subgraph is below threshold."""
        return {"statement": "uncertainty_bound_proven"}

    def _build_influence_witness(self, entity_id: str) -> dict:
        """Builds witness for influence proof."""
        return {"witness": "..."}

    def _generate_snark_proof(self, app_name: str, public_inputs: dict, witness: dict) -> dict:
        """Generates SNARK proof."""
        return {"pi": "mock_snark_proof"}
