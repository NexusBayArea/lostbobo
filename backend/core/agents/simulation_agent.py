from __future__ import annotations

import uuid

from backend.core.agents.base_agent import BaseAgent
from backend.core.models.hypothesis import Hypothesis


class SimulationAgent(BaseAgent):
    """Generates hypotheses from simulation runs."""

    agent_id: str = "simulation"

    async def generate(self, query: str, context: list[dict]) -> list[Hypothesis]:
        hypotheses = []
        for i in range(3):
            h = Hypothesis(
                id=str(uuid.uuid4()),
                claim={"query": query, "variant": f"sim_{i}"},
                reasoning=f"Simulation path {i+1}",
                sim_params={"temp": 298 + i * 5, "c_rate": 1.0 + i * 0.5},
                simulation_score=0.75 + (i * 0.08),
            )
            hypotheses.append(h)
        return hypotheses
