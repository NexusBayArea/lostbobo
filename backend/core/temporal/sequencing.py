from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class SequencedEvent(BaseModel):
    """Causally ordered event with sequence number."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime
    sequence_number: int
    causal_parent: str | None = None
    source: str
    event_type: str
    payload: dict[str, Any]
    vector_clock: dict[str, int] = Field(default_factory=dict)
