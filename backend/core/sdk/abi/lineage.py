from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class LineageRecord(BaseModel):
    plugin_name: str
    capability: str
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    trace_id: str
    parent_trace_id: str | None = None
    deterministic_hash: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LineageQuery(BaseModel):
    trace_id: str | None = None
    plugin_name: str | None = None
    capability: str | None = None
    since: datetime | None = None
    until: datetime | None = None
    limit: int = 100
