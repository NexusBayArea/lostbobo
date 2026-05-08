from dataclasses import dataclass
from typing import Any

import structlog

from backend.core.extractor.claim_extractor import ClaimExtractor
from backend.core.supabase_job_store import SupabaseJobStore
from backend.kernel.kernel import Kernel
from backend.security.leak_detection.detector import LeakageDetector
from backend.security.prompt_guard.guard import PromptGuard
from backend.security.verification.claim_verifier import ClaimVerifier

log = structlog.get_logger(__name__)


@dataclass
class TrustVerificationResult:
    trust_score: float
    decision: str  # ALLOW | WARN | BLOCK
    risk_flags: list[str]
    provenance_hash: str
    certificate_id: str | None = None


class TrustRuntimeService:
    """Kernel-centered Trust Runtime Layer."""

    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.supabase = SupabaseJobStore()
        self.claim_extractor = ClaimExtractor()
        self.claim_verifier = ClaimVerifier()
        self.leak_detector = LeakageDetector()
        self.prompt_guard = PromptGuard()

    async def verify(self, payload: dict[str, Any]) -> TrustVerificationResult:
        """Main entry point — called via Kernel Command Bus."""
        job_id = payload.get("job_id") or await self.supabase.create_job("trust_verify", payload)

        input_text = str(payload.get("input", ""))

        # 1. Claim Extraction
        claim_result = await self.claim_extractor.extract(input_text)

        # 2. Leak & Prompt Guard (early safety)
        leaks = await self.leak_detector.scan(input_text)
        guard_result = await self.prompt_guard.detect(input_text)

        if leaks or not guard_result.get("safe", True):
            risk_flags = ["leak_detected"] if leaks else ["prompt_injection"]
            certificate = await self._save_certificate(job_id, 0.0, "BLOCK", risk_flags, payload.get("tenant_id"))
            return TrustVerificationResult(
                trust_score=0.0,
                decision="BLOCK",
                risk_flags=risk_flags,
                provenance_hash="",
                certificate_id=certificate["id"],
            )

        # 3. Full Claim Verification
        verification = await self.claim_verifier.verify(claim_result, context=payload.get("context", {}))

        # 4. Final Trust Score
        final_score = verification.confidence * (0.0 if verification.risk_flags else 1.0)

        decision = "ALLOW" if final_score >= 0.75 else "WARN" if final_score >= 0.45 else "BLOCK"

        certificate = await self._save_certificate(
            job_id=job_id,
            score=final_score,
            decision=decision,
            risk_flags=verification.risk_flags + (leaks or []),
            tenant_id=payload.get("tenant_id"),
        )

        return TrustVerificationResult(
            trust_score=final_score,
            decision=decision,
            risk_flags=verification.risk_flags,
            provenance_hash=verification.provenance_hash,
            certificate_id=certificate["id"],
        )

    async def _save_certificate(
        self, job_id: str, score: float, decision: str, risk_flags: list[str], tenant_id: str
    ) -> dict[str, Any]:
        return await self.supabase.save_trust_certificate(
            {
                "job_id": job_id,
                "trust_score": score,
                "decision": decision,
                "risk_flags": risk_flags,
                "tenant_id": tenant_id,
            }
        )
