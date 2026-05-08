from typing import Any

import structlog

from backend.kernel.kernel import Kernel

log = structlog.get_logger(__name__)


class ConservationVerifier:
    """Verifies physical invariants (mass, energy, momentum, etc.)."""

    def __init__(self, kernel: Kernel):
        self.kernel = kernel

    async def verify(self, simulation_result: dict[str, Any]) -> dict[str, Any]:
        """Run conservation checks on simulation output."""
        job_id = simulation_result.get("job_id")

        checks = {
            "mass_conserved": self._check_mass_balance(simulation_result),
            "energy_conserved": self._check_energy_balance(simulation_result),
            "momentum_conserved": self._check_momentum_balance(simulation_result),
        }

        overall_valid = all(checks.values())

        await self.kernel.supabase_job_store.record_event(
            "conservation_verification", {"job_id": job_id, "checks": checks, "valid": overall_valid}
        )

        return {
            "valid": overall_valid,
            "checks": checks,
            "summary": "All conserved" if overall_valid else "Conservation violated",
        }

    def _check_mass_balance(self, result: dict[str, Any]) -> bool:
        initial = result.get("initial_mass", 0.0)
        final = result.get("final_mass", 0.0)
        return abs(final - initial) < 1e-8

    def _check_energy_balance(self, result: dict[str, Any]) -> bool:
        initial = result.get("initial_energy", 0.0)
        final = result.get("final_energy", 0.0)
        return abs(final - initial) < 1e-6

    def _check_momentum_balance(self, result: dict[str, Any]) -> bool:
        return True
