from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from backend.core.probability.prediction import Prediction


class Observation(BaseModel):
    timestamp: datetime
    source: str
    payload: dict[str, Any]
    provenance: list[str] = Field(default_factory=list)


class Action(BaseModel):
    action_type: str
    payload: dict[str, Any]
    confidence: float = 1.0
    predicted_impact: Prediction | None = None


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
        """Receive world state changes / events."""

    @abstractmethod
    async def reason(self) -> dict[str, Any]:
        """Internal reasoning step — returns structured thoughts."""

    @abstractmethod
    async def forecast(self) -> Prediction:
        """Produce a calibrated Prediction object."""

    @abstractmethod
    async def act(self) -> Action | None:
        """Decide on and return an action (optional)."""

    @abstractmethod
    async def evaluate(self, outcome: Any) -> EvaluationResult:
        """Self-evaluate after outcome is known."""
