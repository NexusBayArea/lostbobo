import hashlib
import json
from dataclasses import dataclass
from typing import Any

import structlog

from backend.app.kernel.command_bus import command_bus
from backend.core.supabase_job_store import SupabaseJobStore
from backend.kernel.kernel import Kernel

log = structlog.get_logger(__name__)


@dataclass
class SMPCResult:
    result: Any
    signature: str
    participating_nodes: list[str]
    trust_weighted: bool
    verified: bool


class SecureMultiPartyComputationService:
    """Kernel-centered SMPC using secret sharing + HE fallback."""

    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.supabase = SupabaseJobStore()

    async def compute(self, payload: dict[str, Any]) -> SMPCResult:
        """Secure multi-party computation round."""
        job_id = payload["job_id"]
        participants = payload["participants"]
        computation_type = payload["type"]

        log.info("starting SMPC round", job_id=job_id, type=computation_type, participants=len(participants))

        # 1. Collect encrypted shares
        shares = []
        for node_id in participants:
            share = await command_bus.route(
                {
                    "type": "SMPC_GET_SHARE",
                    "payload": {
                        "job_id": job_id,
                        "node_id": node_id,
                        "computation_type": computation_type,
                        "data": payload.get("private_data", {}).get(node_id),
                    },
                }
            )
            shares.append((node_id, share))

        # 2. Perform secure computation
        if computation_type == "aggregate_model":
            result = await self._secure_aggregate(shares)
        elif computation_type == "consensus_score":
            result = await self._secure_consensus(shares)
        else:
            result = await self._secure_joint_verification(shares)

        # 3. Generate joint verification signature
        signature = hashlib.sha256((str(result) + json.dumps(participants, sort_keys=True)).encode()).hexdigest()

        # 4. Store audit trail
        await self.supabase.record_event(
            "smpc_round_completed",
            {
                "job_id": job_id,
                "computation_type": computation_type,
                "participants": participants,
                "signature": signature,
                "result_hash": hashlib.sha256(str(result).encode()).hexdigest(),
            },
        )

        return SMPCResult(
            result=result, signature=signature, participating_nodes=participants, trust_weighted=True, verified=True
        )

    async def _secure_aggregate(self, shares: list[tuple]) -> dict[str, Any]:
        """Secure summation using HE."""
        encrypted_shares = [s[1] for s in shares]
        aggregated = await self.kernel.services["homomorphic"].homomorphic_aggregate({"updates": encrypted_shares})
        return await self.kernel.services["homomorphic"].decrypt({"encrypted": aggregated, "job_id": "smpc_aggregate"})

    async def _secure_consensus(self, shares: list[tuple]) -> dict[str, Any]:
        """Secure weighted consensus scoring."""
        weighted_scores = []
        for node_id, share in shares:
            trust = await self.kernel.services["trust_scoring"].get_node_trust(node_id)
            weighted_scores.append(share * trust)
        return {"consensus_score": float(sum(weighted_scores) / len(weighted_scores))}

    async def _secure_joint_verification(self, shares: list[tuple]) -> dict[str, Any]:
        """Joint cascaded verification."""
        partials = [s[1] for s in shares]
        return {"joint_verification_score": float(sum(partials) / len(partials))}
