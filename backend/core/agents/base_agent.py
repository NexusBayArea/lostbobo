from __future__ import annotations

from abc import ABC, abstractmethod

from backend.core.models.hypothesis import Hypothesis


class BaseAgent(ABC):
    """All agents must return Hypothesis objects only."""

    agent_id: str = "base"

    @abstractmethod
    async def generate(self, query: str, context: list[dict]) -> list[Hypothesis]:
        pass
