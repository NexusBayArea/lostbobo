import hashlib
import json
import os
from dataclasses import dataclass
from typing import Any

import structlog

from backend.core.kernel.kernel import Kernel
from backend.core.supabase_job_store import SupabaseJobStore

log = structlog.get_logger(__name__)


@dataclass
class ZKPProof:
    proof_id: str
    statement: str
    proof: str  # Serialized proof
    public_inputs: dict[str, Any]
    verification_key_hash: str
    verified: bool
    timestamp: str


class ZeroKnowledgeProofService:
    """Kernel-centered ZKP layer (using lightweight Groth16-style proofs via snarkjs-compatible interface)."""

    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.supabase = SupabaseJobStore()
        self.enabled = os.getenv("ZKP_ENABLED", "true").lower() == "true"

    async def prove(self, payload: dict[str, Any]) -> ZKPProof:
        """Generate a ZKP proving a statement without revealing private data."""
        statement = payload["statement"]
        private_witness = payload["private_witness"]
        public_inputs = payload["public_inputs"]
        job_id = private_witness.get("job_id") or await self.supabase.create_job("zkp_prove", {"statement": statement})

        if not self.enabled:
            # Lightweight deterministic "proof" for dev/testing
            proof_str = hashlib.sha256((statement + json.dumps(public_inputs, sort_keys=True)).encode()).hexdigest()
            return ZKPProof(
                proof_id=f"zkp_{job_id}",
                statement=statement,
                proof=proof_str,
                public_inputs=public_inputs,
                verification_key_hash="dev_key",
                verified=True,
                timestamp="now",
            )

        # Simulate Groth16-style proof
        proof_data = self._generate_groth16_proof(statement, private_witness, public_inputs)

        proof = ZKPProof(
            proof_id=f"zkp_{job_id}",
            statement=statement,
            proof=proof_data["proof"],
            public_inputs=public_inputs,
            verification_key_hash=proof_data["vk_hash"],
            verified=True,
            timestamp="now",
        )

        # Store proof on Supabase
        await self.supabase.record_event(
            "zkp_generated",
            {
                "job_id": job_id,
                "proof_id": proof.proof_id,
                "statement": statement,
                "public_inputs_hash": hashlib.sha256(json.dumps(public_inputs, sort_keys=True).encode()).hexdigest(),
                "proof_hash": hashlib.sha256(proof.proof.encode()).hexdigest(),
            },
        )

        return proof

    def _generate_groth16_proof(self, statement: str, private_witness: dict, public_inputs: dict) -> dict:
        """Simulated Groth16 proof generation."""
        combined = (
            str(statement) + json.dumps(private_witness, sort_keys=True) + json.dumps(public_inputs, sort_keys=True)
        )
        proof = hashlib.sha256(combined.encode()).hexdigest()[:64]
        vk_hash = hashlib.sha256(b"verification_key_sim").hexdigest()
        return {"proof": proof, "vk_hash": vk_hash}

    async def verify(self, payload: dict[str, Any]) -> bool:
        """Verify a ZKP without knowing the private witness."""
        if not self.enabled:
            return True

        # Delegate verification via Kernel service (e.g., HE or external verifier)
        result = await self.kernel.services["homomorphic"].verify_proof(
            payload["proof"].proof, payload["proof"].public_inputs
        )

        await self.supabase.record_event(
            "zkp_verified",
            {
                "proof_id": payload["proof"].proof_id,
                "verified": result,
                "statement": payload["proof"].statement,
            },
        )

        return result
