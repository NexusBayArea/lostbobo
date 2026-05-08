from typing import Any

from backend.kernel.dag.node import SimulationNode
from backend.kernel.plugins.quantum_chemistry.plugin import QuantumChemistryPlugin


class QuantumChemistryNode(SimulationNode):
    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        plugin = QuantumChemistryPlugin()
        await plugin.initialize(context)
        result = await plugin.step(context.get("dt", 0.1), context)
        context["quantum_results"] = result
        return result
