from __future__ import annotations

import uuid

from backend.core.agents.base_agent import BaseAgent
from backend.core.models.hypothesis import Hypothesis


class ReasoningAgent(BaseAgent):
    """Generates hypotheses from pure reasoning."""

    agent_id: str = "reasoning"

    async def generate(self, query: str, context: list[dict]) -> list[Hypothesis]:
        hypotheses = []
        for i in range(3):
            h = Hypothesis(
                id=str(uuid.uuid4()),
                claim={"query": query, "variant": f"reasoning_{i}"},
                reasoning=f"Reasoning path {i+1} for: {query}",
                plausibility_score=0.7 + (i * 0.1),
            )
            hypotheses.append(h)
        return hypotheses
