"""Simulation Validation Layer — 3-tier checks for LLM → Simulation pipeline."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np

log = logging.getLogger(__name__)


@dataclass
class ValidationRule:
    id: str
    category: str
    prompt: str
    judge: str
    ground_truth_range: tuple[float, float] | None = None
    ground_truth_contains: list[str] | None = None
    ground_truth_numeric: float | None = None
    tolerance: float = 0.1


class SimulationValidator:
    """Validates LLM-extracted parameters, physical consistency, and simulation outputs."""

    def __init__(self):
        self.rules = self._load_default_rules()

    def _load_default_rules(self) -> list[ValidationRule]:
        return [
            ValidationRule(
                id="lithium_diffusion_coeff",
                category="simulation_parameters",
                prompt="Diffusion coefficient of lithium in graphite?",
                judge="range_numeric",
                ground_truth_range=(1e-12, 1e-9),
            ),
            ValidationRule(
                id="mass_conservation",
                category="physics",
                prompt="Does lithium plating violate mass conservation?",
                judge="contains_all",
                ground_truth_contains=["conservation", "lithium", "electrode"],
            ),
            ValidationRule(
                id="plating_current",
                category="simulation_output",
                prompt="Max plating current density?",
                judge="numeric",
                ground_truth_numeric=2.1,
                tolerance=0.2,
            ),
        ]

    async def validate_parameters(self, extracted_params: dict) -> dict[str, Any]:
        """Tier 1: Parameter validation."""
        results = {}
        for rule in self.rules:
            if rule.category != "simulation_parameters":
                continue
            passed = self._apply_judge(rule, extracted_params)
            results[rule.id] = {"passed": passed, "rule": rule.id, "value": extracted_params.get(rule.id)}
        return results

    async def validate_physics(self, simulation_output: dict) -> dict[str, Any]:
        """Tier 2: Physical consistency."""
        results = {}
        for rule in self.rules:
            if rule.category != "physics":
                continue
            passed = self._apply_judge(rule, simulation_output)
            results[rule.id] = {"passed": passed, "rule": rule.id}
        return results

    async def validate_output(self, output: dict) -> dict[str, Any]:
        """Tier 3: Simulation result validation."""
        results = {}
        for rule in self.rules:
            if rule.category != "simulation_output":
                continue
            passed = self._apply_judge(rule, output)
            results[rule.id] = {"passed": passed, "rule": rule.id}
        return results

    def _apply_judge(self, rule: ValidationRule, data: dict) -> bool:
        value = data.get(rule.id)
        if value is None:
            return False

        if rule.judge == "range_numeric" and rule.ground_truth_range:
            lo, hi = rule.ground_truth_range
            return lo <= float(value) <= hi

        if rule.judge == "contains_all" and rule.ground_truth_contains:
            text = str(value).lower()
            return all(term.lower() in text for term in rule.ground_truth_contains)

        if rule.judge == "numeric" and rule.ground_truth_numeric is not None:
            return abs(float(value) - rule.ground_truth_numeric) <= rule.tolerance

        return True


@dataclass
class SimulationMetadata:
    run_id: str
    user_id: str
    model_used: str
    rag_version: str
    simulation_engine: str = "MFEM"
    parameters_hash: str
    timestamp: str
    validation_passed: bool
    trust_score: float = 0.0


def compress_simulation(data: np.ndarray) -> bytes:
    """ZFP compression for simulation grids/fields."""
    try:
        import zfpy

        return zfpy.compress_numpy(data, tolerance=1e-6)
    except ImportError:
        return data.tobytes()


def decompress_simulation(blob: bytes, shape: tuple[int, ...]) -> np.ndarray:
    """Fast decompression."""
    try:
        import zfpy

        return zfpy.decompress_numpy(blob)
    except ImportError:
        return np.frombuffer(blob, dtype=np.float64).reshape(shape)
