"""Canonical event schema — immutable after creation."""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.core.runtime.event_fabric.vector_clock import VectorClock


class EventPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"


class SimHPCEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = Field(...)
    timestamp: float = Field(default_factory=time.time)
    causal_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    source_plugin: str = Field(...)
    priority: EventPriority = Field(default=EventPriority.NORMAL)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    payload: dict[str, Any] = Field(default_factory=dict)
    provenance_hash: str | None = None
    vector_clock: VectorClock = Field(default_factory=VectorClock)

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        return float(max(0.0, min(1.0, v)))

    @model_validator(mode="before")
    @classmethod
    def coerce_vector_clock(cls, data: Any) -> Any:
        if isinstance(data, dict) and isinstance(data.get("vector_clock"), dict):
            data["vector_clock"] = VectorClock(data["vector_clock"])
        return data

    def seal(self) -> SimHPCEvent:
        self.vector_clock.increment(self.source_plugin)
        data = self.model_dump(exclude={"provenance_hash"})
        data["vector_clock"] = dict(self.vector_clock)
        content = json.dumps(data, sort_keys=True, default=str)
        h = hashlib.sha256(content.encode()).hexdigest()
        compact_causal = hashlib.sha256(json.dumps(dict(self.vector_clock), sort_keys=True).encode()).hexdigest()[:16]
        sealed_data = {**data, "provenance_hash": h, "causal_id": compact_causal}
        return SimHPCEvent.model_validate(sealed_data)
