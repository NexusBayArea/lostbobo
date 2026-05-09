from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from backend.core.agents.contracts.actions import Action
from backend.core.agents.contracts.forecasts import ForecastRequest, ForecastResponse
from backend.core.agents.contracts.observations import Observation
from backend.core.agents.contracts.reasoning import ReasoningTrace


class EvaluationResult(BaseModel):
    score: float
    brier_score: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class BaseAgent(ABC):
    """Universal contract for all agents in the SimHPC runtime."""

    id: str
    name: str
    domain: str

    def __init__(self, name: str, domain: str):
        self.id = str(uuid4())
        self.name = name
        self.domain = domain

    @abstractmethod
    async def observe(self, observation: Observation) -> None:
        """Receive standardized observations."""

    @abstractmethod
    async def reason(self) -> list[ReasoningTrace]:
        """Produce auditable reasoning trace."""

    @abstractmethod
    async def forecast(self, request: ForecastRequest | None = None) -> ForecastResponse:
        """Return structured forecast using Prediction object."""

    @abstractmethod
    async def act(self) -> Action | None:
        """Emit standardized actions (routed through runtime)."""

    @abstractmethod
    async def evaluate(self, outcome: Any, ground_truth: Any | None = None) -> EvaluationResult:
        """Self-evaluation using proper scoring rules."""
