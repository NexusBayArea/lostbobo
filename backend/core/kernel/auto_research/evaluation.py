"""Evaluation Engine — multi-objective scoring with uncertainty."""

from __future__ import annotations

from typing import Any


def compute_score(result: dict[str, Any]) -> float:
    """Multi-objective function (configurable weights)."""
    w = result.get("weights", {"performance": 0.5, "cost": -0.2, "risk": -0.2, "robustness": 0.1})

    score = (
        w["performance"] * result.get("performance", 0)
        + w["cost"] * result.get("cost", 0)
        + w["risk"] * result.get("risk", 0)
        + w["robustness"] * result.get("robustness", 0)
    )

    uncertainty = result.get("uncertainty_std", 0)
    score -= 0.15 * uncertainty

    return score


def run_simulation_gate(result: dict[str, Any]) -> bool:
    """Stress test + edge-case validation before commit."""
    if result.get("performance", 0) < 0:
        return False
    if result.get("uncertainty_std", 0) > result.get("max_uncertainty", 0.3):
        return False
    return True
