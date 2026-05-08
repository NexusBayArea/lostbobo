from typing import Any

import structlog

log = structlog.get_logger(__name__)


class Psi4Backend:
    """Mock Psi4 backend for environments where Psi4 cannot be built."""

    def __init__(self):
        self.results = {}
        self.options = {"basis": "def2-svp", "dft_functional": "b3lyp", "memory": "2 GB"}

    async def initialize(self, context: dict[str, Any]) -> bool:
        """Initialize Psi4 molecule from geometry and settings."""
        log.info("Psi4 initialized (Mock Mode)")
        self.results = {"energy": -76.2, "backend": "psi4_mock", "converged": True}
        return True

    async def step(self, dt: float, exchanged: dict[str, Any]) -> dict[str, Any]:
        """Run Psi4 calculation with classical coupling data."""
        self.results = {
            "energy": -76.2,
            "forces": [[0.0, 0.0, 0.0]],
            "dipole": [0.8, 0.4, 0.2],
            "homo_lumo_gap": 3.1,
            "backend": "psi4_mock",
            "converged": True,
        }
        log.info("Psi4 calculation completed (Mock Mode)")
        return self.results

    async def export_state(self) -> dict[str, Any]:
        return self.results

    async def validate(self) -> dict[str, Any]:
        return {"valid": self.results.get("energy", -1000) < 0, "issues": []}

    async def checkpoint(self) -> str:
        return "psi4_mock_checkpoint"
