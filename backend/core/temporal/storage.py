"""Time-versioned canonical world state storage."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class TemporalState(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime
    uncertainty_snapshot: dict[str, float] = Field(default_factory=dict)
    regime: str = "normal"
    metadata: dict[str, Any] = Field(default_factory=dict)
    causal_id: str = ""
    provenance_event_ids: list[str] = Field(default_factory=list)
