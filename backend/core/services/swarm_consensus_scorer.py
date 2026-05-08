from dataclasses import dataclass
from typing import Any

import numpy as np
import structlog

from backend.core.supabase_job_store import SupabaseJobStore
from backend.kernel.kernel import Kernel

log = structlog.get_logger(__name__)


@dataclass
class SwarmConsensusScore:
    overall_consensus_score: float
    agreement_rate: float
    diversity_score: float
    confidence_coherence: float
    contradiction_rate: float
    risk_level: str
    recommendation: str
    metadata: dict[str, Any]


class SwarmConsensusScorer:
    """Evaluates swarm consensus quality to prevent emergent hallucination."""

    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.supabase = SupabaseJobStore()

    async def score(self, payload: dict[str, Any]) -> SwarmConsensusScore:
        job_id = payload.get("job_id")
        agent_results = payload.get("agent_results", {})
        fused_context = payload.get("fused_context", {})

        if len(agent_results) < 2:
            return SwarmConsensusScore(0.0, 0.0, 1.0, 0.0, 0.0, "HIGH", "ABORT", {})

        # 1. Agreement Rate
        opinions = [str(r.get("final_output", r)) for r in agent_results.values()]
        agreement_rate = self._compute_agreement_rate(opinions)

        # 2. Diversity Score
        diversity_score = self._compute_diversity(opinions)

        # 3. Confidence Coherence
        confidence_coherence = self._compute_confidence_coherence(agent_results)

        # 4. Contradiction Rate
        contradiction_rate = await self._detect_contradictions(agent_results, fused_context)

        # Weighted consensus score
        consensus_score = (
            agreement_rate * 0.35
            + diversity_score * 0.25
            + confidence_coherence * 0.25
            + (1.0 - contradiction_rate) * 0.15
        )

        risk_level = "LOW" if consensus_score > 0.75 else "MEDIUM" if consensus_score > 0.5 else "HIGH"
        recommendation = "PROCEED" if risk_level == "LOW" else "REVIEW" if risk_level == "MEDIUM" else "ABORT"

        score = SwarmConsensusScore(
            overall_consensus_score=float(consensus_score),
            agreement_rate=float(agreement_rate),
            diversity_score=float(diversity_score),
            confidence_coherence=float(confidence_coherence),
            contradiction_rate=float(contradiction_rate),
            risk_level=risk_level,
            recommendation=recommendation,
            metadata={"agent_count": len(agent_results), "job_id": job_id},
        )

        await self.supabase.record_event("swarm_consensus_scored", {"job_id": job_id, "score": score.__dict__})

        return score

    def _compute_agreement_rate(self, opinions: list[str]) -> float:
        if not opinions:
            return 0.0
        unique = len(set(opinions))
        return float(1.0 - (unique - 1) / len(opinions))

    def _compute_diversity(self, opinions: list[str]) -> float:
        if len(opinions) < 2:
            return 1.0
        return float(min(1.0, len(set(" ".join(opinions).split())) / 50.0))

    def _compute_confidence_coherence(self, agent_results: dict[str, Any]) -> float:
        confidences = [r.get("confidence", 0.5) for r in agent_results.values()]
        if not confidences:
            return 0.0
        mean_conf = np.mean(confidences)
        std_conf = np.std(confidences)
        return float(mean_conf * (1.0 - std_conf))

    async def _detect_contradictions(self, agent_results: dict[str, Any], fused_context: dict[str, Any]) -> float:
        contradictions = 0
        for result in agent_results.values():
            is_contradicting = await self.kernel.services["world_model"].check_contradiction(
                result.get("final_output", ""), fused_context
            )
            if is_contradicting:
                contradictions += 1
        return float(contradictions / max(len(agent_results), 1))
