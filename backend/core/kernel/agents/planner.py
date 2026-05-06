"""Planner Agent — uses Kernel for all execution."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from backend.core.kernel.kernel import Kernel

from backend.core.models.hypothesis import Hypothesis
from backend.core.simulation.runner import SimulationRunner


class PlannerAgent:
    def __init__(self, kernel: "Kernel"):
        self.kernel = kernel
        self.runner = SimulationRunner()

    async def run(self, input_data: dict[str, Any]) -> Hypothesis:
        hyp = Hypothesis()
        hyp.sim_params = input_data
        result = await self.runner.run(hyp)

        await self.kernel.execute(
            {
                "type": "MEMORY_RECORD",
                "payload": {
                    "type": "decision",
                    "content": {"plan": result, "goal": input_data.get("goal")},
                },
            }
        )

        return result
