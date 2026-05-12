from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ProtocolEnvelope(BaseModel):
    envelope_id: str = Field(default_factory=lambda: uuid4().hex)
    protocol: str
    action: str
    target: str
    tenant_id: str
    source: str
    correlation_id: str
    protocol_version: str = "1.0"
    timestamp: float = Field(default_factory=time.time)
    payload: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)
    replayable: bool = True
    lineage_enabled: bool = True
    timeout_seconds: int = 300
    causality_parent: str | None = None
    trace_id: str | None = None
    dag_id: str | None = None
    node_id: str | None = None
