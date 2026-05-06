"""Canonical Hypothesis — single source of truth."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Hypothesis:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: str | None = None

    claim: dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""

    sim_params: dict[str, Any] = field(default_factory=dict)
    sim_result: dict[str, Any] | None = None

    plausibility_score: float = 0.0
    math_score: float = 0.0
    simulation_score: float = 0.0
    robustness_score: float = 0.0
    rag_score: float = 0.0
    consensus_score: float = 0.0
    trust_score: float = 0.0

    stage: str = "init"
    agent_id: str = ""
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def update_trust(self) -> float:
        """Centralized trust score."""
        self.trust_score = (
            0.40 * self.simulation_score
            + 0.25 * self.robustness_score
            + 0.20 * self.rag_score
            + 0.15 * self.consensus_score
        )
        return round(self.trust_score, 4)
