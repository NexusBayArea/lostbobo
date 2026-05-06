from __future__ import annotations

import uuid

from backend.core.agents.base_agent import BaseAgent
from backend.core.models.hypothesis import Hypothesis


class RAGAgent(BaseAgent):
    """Generates hypotheses from RAG context."""

    agent_id: str = "rag"

    async def generate(self, query: str, context: list[dict]) -> list[Hypothesis]:
        hypotheses = []
        for i, ctx_item in enumerate(context[:3]):
            h = Hypothesis(
                id=str(uuid.uuid4()),
                claim={"query": query, "source": ctx_item.get("id"), "variant": "rag"},
                reasoning=f"RAG path from context {i+1}",
                rag_score=0.8 + (i * 0.05),
            )
            hypotheses.append(h)
        return hypotheses
