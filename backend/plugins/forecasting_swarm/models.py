from __future__ import annotations

import uuid
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class AgentRole(str, Enum):
    TREND = "trend"
    STRUCTURAL = "structural"
    DISTRIBUTIONAL = "distributional"
    CONTRARIAN = "contrarian"


class AgentOutput(BaseModel):
    agent_id: str
    role: AgentRole
    point_estimate: float = Field(ge=0.0, le=1.0)
    confidence_interval: tuple[float, float] = Field(min_length=2, max_length=2)
    weight: float = Field(ge=0.0)
    reasoning_summary: str = ""
    calibration_score: float = Field(ge=0.0, le=1.0, default=0.5)
    novelty_score: float = Field(ge=0.0, le=1.0, default=0.5)

    @field_validator("confidence_interval", mode="before")
    @classmethod
    def validate_ci(cls, v):
        lo, hi = v[0], v[1]
        if lo > hi:
            raise ValueError("CI lower bound must be <= upper bound")
        return (float(lo), float(hi))


class AggregatedForecast(BaseModel):
    question_id: str
    final_estimate: float
    confidence_interval: tuple[float, float]
    consensus_score: float = Field(ge=0.0, le=1.0)
    dissent_detected: bool
    dissenting_agents: list[str] = Field(default_factory=list)
    agent_count: int
    calibration_coverages: list[float] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class PredictionQuestion(BaseModel):
    question_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question_text: str
    resolution_criteria: str = ""
    category: str = "general"
    time_horizon_days: int = Field(ge=1, default=30)
    background_context: str = ""
    relevant_agents: list[AgentRole] | None = None
