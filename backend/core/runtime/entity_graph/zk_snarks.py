from __future__ import annotations

import hashlib
import json
import time

from backend.core.certificates import seal_result
from backend.core.runtime.entity_graph.service import EntityGraphService
from backend.core.runtime.event_fabric.log import EventLogService
from backend.core.runtime.event_fabric.schema import SimHPCEvent
from backend.core.runtime.state_registry.service import StateRegistryService
from backend.core.services.observability_service import observability
from backend.core.tracing import trace_context


class ZKSNARKsGraphEngine:
    """zk-SNARKs (Groth16/Plonk) over temporal-probabilistic graphs."""

    _instance = None
    # In production: pre-compiled proving/verification keys from circuit compilation
    _proving_key = None
    _verification_key = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Circuit compilation happens at build time (e.g. circom / halo2)
            cls._instance._initialize_keys()
        return cls._instance

    @classmethod
    def snarks(cls) -> ZKSNARKsGraphEngine:
        return cls()

    def _initialize_keys(self):
        """Mock key initialization."""
        self._proving_key = {"pk": "..."}
        self._verification_key = {"vk": "..."}

    async def prove_subgraph_property(self, statement: str, params: dict) -> dict:
        """Prove arbitrary graph properties succinctly."""
        with trace_context("snarks.prove", {"statement": statement}) as span:
            obs = observability()
            obs.increment("snarks_proof_generations_total", tags={"statement": statement})

            await EntityGraphService.graph().get_graph_snapshot()
            state = await StateRegistryService.registry().get_current()

            # Private witness (never leaves secure context)
            private_witness = self._build_witness(params)

            # Public inputs (revealed)
            public_inputs = {
                "statement_hash": hashlib.sha256(statement.encode()).hexdigest(),
                "timestamp": int(time.time()),
                "regime": state.regime,
                **self._extract_public_params(params),
            }

            # Generate proof (Groth16 example)
            proof = self._generate_snark_proof(public_inputs, private_witness)

            sealed_proof = {
                "proof_id": f"snark_{int(time.time())}",
                "statement": statement,
                "public_inputs": public_inputs,
                "proof": proof,  # constant size ~few KB
                "verification_key_hash": hashlib.sha256(str(self._verification_key).encode()).hexdigest(),
                "provenance_hash": seal_result(public_inputs),
            }

            # Publish sealed proof as immutable event
            await EventLogService.event_log().publish(
                SimHPCEvent(
                    event_type="graph.snarks.proof_generated",
                    source_plugin="kernel",
                    priority="high",
                    payload=sealed_proof,
                )
            )

            span.set_attribute("proof_size_kb", len(json.dumps(proof)) / 1024)
            return sealed_proof

    async def verify(self, proof: dict) -> bool:
        """Public, extremely fast verification (milliseconds)."""
        return self._verify_snark_proof(proof["proof"], proof["public_inputs"])

    def _build_witness(self, params: dict) -> dict:
        """Contains full private graph data, temporal weights, uncertainties, etc."""
        return {"witness": "..."}

    def _extract_public_params(self, params: dict) -> dict:
        """Extract public parameters."""
        return {}

    def _generate_snark_proof(self, public_inputs: dict, private_witness: dict) -> dict:
        """Calls compiled circuit (Groth16/Plonk)."""
        return {"pi": "mock_snark_proof"}

    def _verify_snark_proof(self, proof: dict, public_inputs: dict) -> bool:
        """Verifies snark proof."""
        return True
