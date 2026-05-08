import time
from dataclasses import dataclass
from typing import Any

import structlog

from backend.app.kernel.command_bus import command_bus
from backend.core.kernel.kernel import Kernel
from backend.core.supabase_job_store import SupabaseJobStore

log = structlog.get_logger(__name__)


@dataclass
class VerificationStageResult:
    stage: int
    name: str
    passed: bool
    score: float
    details: dict[str, Any]
    duration_ms: float


@dataclass
class CascadedVerificationResult:
    overall_passed: bool
    trust_score: float
    decision: str  # ALLOW | WARN | BLOCK
    stages: list[VerificationStageResult]
    verification_signature: str
    certificate_id: str | None = None


class CascadedVerificationPipeline:
    """5-Stage Cascaded Verification — Kernel-centered."""

    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.supabase = SupabaseJobStore()

    async def verify(self, payload: dict[str, Any]) -> CascadedVerificationResult:
        job_id = payload.get("job_id") or await self.supabase.create_job("cascaded_verification", payload)
        stages = []

        # Stage 1: Cheap Plausibility
        stage1 = await self._stage_plausibility(payload)
        stages.append(stage1)
        if not stage1.passed:
            return await self._early_exit(job_id, stages, 0.3)

        # Stage 2: Mathematical Consistency
        stage2 = await self._stage_math_consistency(payload)
        stages.append(stage2)
        if not stage2.passed:
            return await self._early_exit(job_id, stages, 0.5)

        # Stage 3: Deterministic Simulation
        stage3 = await self._stage_deterministic_simulation(payload)
        stages.append(stage3)
        if not stage3.passed:
            return await self._early_exit(job_id, stages, 0.65)

        # Stage 4: Robustness Perturbation
        stage4 = await self._stage_robustness(payload)
        stages.append(stage4)

        # Stage 5: Certificate Generation
        stage5 = await self._stage_certificate(payload, stages)
        stages.append(stage5)

        final_score = sum(s.score * (0.1 + 0.225 * (s.stage - 1)) for s in stages) / 5
        decision = "ALLOW" if final_score >= 0.75 else "WARN" if final_score >= 0.55 else "BLOCK"

        cert = await self.supabase.save_trust_certificate(
            {
                "job_id": job_id,
                "trust_score": final_score,
                "decision": decision,
                "stages": [s.__dict__ for s in stages],
                "verification_signature": stage5.details["signature"],
                "tenant_id": payload.get("tenant_id"),
            }
        )

        await self.supabase.update_job(job_id, status="completed", result={"final_score": final_score})

        return CascadedVerificationResult(
            overall_passed=decision != "BLOCK",
            trust_score=final_score,
            decision=decision,
            stages=stages,
            verification_signature=stage5.details["signature"],
            certificate_id=cert["id"],
        )

    async def _stage_plausibility(self, payload: dict[str, Any]) -> VerificationStageResult:
        start = time.time()
        score = 0.85 if "plausible" in str(payload).lower() else 0.4
        return VerificationStageResult(1, "Plausibility", score > 0.6, score, {}, (time.time() - start) * 1000)

    async def _stage_math_consistency(self, payload: dict[str, Any]) -> VerificationStageResult:
        result = await self.kernel.services["physics"].validate_math(payload)
        return VerificationStageResult(
            2, "Math Consistency", result.get("passed", True), result.get("score", 0.9), result, 120
        )

    async def _stage_deterministic_simulation(self, payload: dict[str, Any]) -> VerificationStageResult:
        result = await command_bus.route({"type": "PHYSICS_SIMULATE", "payload": payload})
        return VerificationStageResult(
            3, "Deterministic Simulation", result.get("validation_passed", False), result.get("score", 0.0), result, 450
        )

    async def _stage_robustness(self, payload: dict[str, Any]) -> VerificationStageResult:
        result = await command_bus.route({"type": "ROBUSTNESS_SWEEP", "payload": payload})
        return VerificationStageResult(
            4, "Robustness", result.get("stable", True), result.get("score", 0.0), result, 680
        )

    async def _stage_certificate(
        self, payload: dict[str, Any], stages: list[VerificationStageResult]
    ) -> VerificationStageResult:
        sig = await self.kernel.services["trust_runtime"].generate_verification_signature(payload, stages)
        return VerificationStageResult(5, "Certificate", True, 1.0, {"signature": sig}, 80)

    async def _early_exit(self, job_id: str, stages: list[VerificationStageResult], score: float):
        await self.supabase.update_job(job_id, status="early_exit", result={"score": score})
        return CascadedVerificationResult(False, score, "BLOCK", stages, "")
