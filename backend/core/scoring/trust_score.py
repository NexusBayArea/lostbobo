"""Centralized Trust Score."""

from backend.core.models.hypothesis import Hypothesis


def compute_trust(h: Hypothesis) -> float:
    return 0.40 * h.simulation_score + 0.25 * h.robustness_score + 0.20 * h.rag_score + 0.15 * h.consensus_score
