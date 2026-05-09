from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class Observation(BaseModel):
    """Standardized input to any agent."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str  # "world_state", "event_fabric", "other_agent", ...
    observation_type: str  # "state_update", "event", "forecast_result", ...
    payload: dict[str, Any]
    provenance: list[str] = Field(default_factory=list)  # event_ids
    confidence: float = 1.0
