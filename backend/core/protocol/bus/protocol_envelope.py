from __future__ import annotations

import time
import uuid
from typing import Any

from pydantic import BaseModel, Field


class ProtocolEnvelope(BaseModel):
    envelope_id: str = str(uuid.uuid4())
    protocol: str
    action: str
    tenant_id: str
    source: str
    target: str
    correlation_id: str
    timestamp: float = time.time()
    payload: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)
    replayable: bool = True
    lineage_enabled: bool = True
    timeout_seconds: int = 300
    causality_parent: str | None = None
