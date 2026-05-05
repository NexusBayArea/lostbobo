from __future__ import annotations

import math
import time
import uuid
from enum import TYPE_CHECKING, Enum

import numpy as np
from pydantic import BaseModel, Field, field_validator

if TYPE_CHECKING:
    from backend.runtime.swarm.conformal_bridge import ConformaBridge


class AgentRole(str, Enum):
    BASE_RATE = "base_rate"
    INSIDE_VIEW = "inside_view"
    NEWS_SYNTH = "news_synth"
    ADVERSARIAL = "adversarial"
    CALIBRATION = "calibration"


class AgentOutput(BaseModel):
    agent_role: AgentRole
    probability: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    evidence_ids: list[str] = Field(default_factory=list)
    brier_weight: float = Field(default=1.0, ge=0.0)
    latency_ms: float | None = None

    @field_validator("probability", "confidence")
    @classmethod
    def clamp(cls, v: float) -> float:
        return float(np.clip(v, 1e-6, 1 - 1e-6))


class AggregatedForecast(BaseModel):
    forecast_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question_id: str
    timestamp: float = Field(default_factory=time.time)

    probability: float
    log_odds: float
    conf_lower: float
    conf_upper: float
    coverage_level: float = 0.90

    consensus_score: float
    dissent_flags: list[str] = Field(default_factory=list)
    agent_probabilities: dict[str, float]
    effective_weights: dict[str, float]

    evidence_ids: list[str]
    reasoning_summary: str
    sha256_sealed: str | None = None


def _prob_to_log_odds(p: float) -> float:
    p = float(np.clip(p, 1e-6, 1 - 1e-6))
    return math.log(p / (1.0 - p))


def _log_odds_to_prob(lo: float) -> float:
    return 1.0 / (1.0 + math.exp(-lo))


def _normalise_weights(raw: list[float]) -> list[float]:
    arr = np.array(raw, dtype=np.float64)
    arr = np.clip(arr, 1e-9, None)
    return (arr / arr.sum()).tolist()


class BayesianAggregator:
    DISSENT_THRESHOLD = 0.15

    def __init__(self, coverage: float = 0.90):
        self.coverage = coverage

    def aggregate(
        self,
        question_id: str,
        agent_outputs: list[AgentOutput],
        conformal_bridge: ConformaBridge,
    ) -> AggregatedForecast:
        if not agent_outputs:
            raise ValueError("No agent outputs")

        roles = [a.agent_role.value for a in agent_outputs]
        probs = [a.probability for a in agent_outputs]
        raw_w = [a.brier_weight * a.confidence for a in agent_outputs]
        norm_w = _normalise_weights(raw_w)

        combined_lo = sum(w * _prob_to_log_odds(p) for w, p in zip(norm_w, probs, strict=False))
        combined_prob = _log_odds_to_prob(combined_lo)

        consensus_score = max(0.0, 1.0 - 2.0 * float(np.std(probs)))
        ensemble_mean = float(np.mean(probs))
        dissent_flags = [
            role for role, p in zip(roles, probs, strict=False) if abs(p - ensemble_mean) > self.DISSENT_THRESHOLD
        ]

        lower = combined_prob - 0.15
        upper = combined_prob + 0.15

        all_evidence = list({eid for a in agent_outputs for eid in a.evidence_ids})
        reasoning = "\n\n".join(f"[{a.agent_role.value.upper()}] {a.reasoning}" for a in agent_outputs)

        return AggregatedForecast(
            question_id=question_id,
            probability=round(combined_prob, 6),
            log_odds=round(combined_lo, 6),
            conf_lower=round(lower, 6),
            conf_upper=round(upper, 6),
            consensus_score=round(consensus_score, 4),
            dissent_flags=dissent_flags,
            agent_probabilities=dict(zip(roles, [round(p, 6) for p in probs], strict=False)),
            effective_weights=dict(zip(roles, [round(w, 6) for w in norm_w], strict=False)),
            evidence_ids=all_evidence,
            reasoning_summary=reasoning,
        )
