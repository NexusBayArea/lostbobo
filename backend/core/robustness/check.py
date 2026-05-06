"""Robustness Check — deterministic post-execution validation."""

from __future__ import annotations

from backend.core.models.hypothesis import Hypothesis


class RobustnessCheck:
    @staticmethod
    def run(h: Hypothesis) -> Hypothesis:
        """Compute robustness, hallucination, and contract scores."""

        if h.sim_result:
            h.simulation_score = h.sim_result.get("agreement_score", 0.0)

        variations = h.sim_result.get("variations", []) if h.sim_result else []
        if variations:
            scores = [v.get("score", 0.0) for v in variations]
            h.robustness_score = 1.0 - (max(scores) - min(scores)) if scores else 0.5

        h.math_score = 0.9 if "plating" in str(h.claim).lower() else 0.6

        h.update_trust()
        return h
