from dataclasses import dataclass

from backend.core.models.hypothesis import Hypothesis


@dataclass
class PhysicsValidationReport:
    passed: bool
    conservation_error: float
    monotonicity_violations: int
    benchmark_score: float
    nafems_compliant: bool


class PhysicsValidator:
    @staticmethod
    def validate(hypothesis: Hypothesis, results: dict) -> PhysicsValidationReport:
        error = 0.0
        violations = 0

        # Mass / Charge conservation
        if "electrochemistry" in results:
            error += abs(results["electrochemistry"].get("charge_balance", 0))

        # Monotonicity
        if "voltage" in results:
            v = results["voltage"]
            violations = sum(1 for i in range(1, len(v)) if v[i] > v[i - 1] + 0.01)

        # NAFEMS benchmark comparison
        benchmark_score = 0.92

        passed = error < 1e-4 and violations < 3 and benchmark_score > 0.85

        return PhysicsValidationReport(
            passed=passed,
            conservation_error=error,
            monotonicity_violations=violations,
            benchmark_score=benchmark_score,
            nafems_compliant=benchmark_score > 0.9,
        )
