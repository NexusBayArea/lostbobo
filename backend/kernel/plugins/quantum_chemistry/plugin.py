from typing import Any

from backend.kernel.abi.plugin import PhysicsPlugin
from backend.kernel.plugins.quantum_chemistry.backends.orca_backend import OrcaBackend
from backend.kernel.plugins.quantum_chemistry.backends.psi4_backend import Psi4Backend
from backend.kernel.plugins.quantum_chemistry.backends.pyscf_backend import PySCFBackend


class QuantumChemistryPlugin(PhysicsPlugin):
    name = "quantum_chemistry"

    def __init__(self):
        self.backends = {"pyscf": PySCFBackend(), "psi4": Psi4Backend(), "orca": OrcaBackend()}
        # Priority: ORCA -> Psi4 -> PySCF
        self.active_backend = "orca"

    async def initialize(self, context: dict[str, Any]) -> bool:
        backend_name = context.get("quantum_backend", self.active_backend)
        if backend_name not in self.backends:
            backend_name = self.active_backend
        self.active_backend = backend_name
        return await self.backends[backend_name].initialize(context)

    async def step(self, dt: float, exchanged: dict[str, Any]) -> dict[str, Any]:
        return await self.backends[self.active_backend].step(dt, exchanged)

    async def export_state(self) -> dict[str, Any]:
        return await self.backends[self.active_backend].export_state()

    async def validate(self) -> dict[str, Any]:
        return await self.backends[self.active_backend].validate()

    async def checkpoint(self) -> str:
        return await self.backends[self.active_backend].checkpoint()
