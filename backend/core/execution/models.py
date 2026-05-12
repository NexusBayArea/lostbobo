from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ExecutionPriority(str, Enum):
    INTERACTIVE = "interactive"
    BACKGROUND = "background"
    SIMULATION = "simulation"
    REPLAY = "replay"
    PLUGIN = "plugin"


class ExecutionStatus(str, Enum):
    QUEUED = "queued"
    LEASED = "leased"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionRequest(BaseModel):
    execution_id: str = Field(default_factory=lambda: uuid4().hex)
    tenant_id: str
    plugin_name: str
    dag_id: str | None = None
    capability: str
    inputs: dict[str, Any] = {}
    priority: ExecutionPriority = ExecutionPriority.SIMULATION
    timeout_seconds: int = 3600
    checkpoint_enabled: bool = True
    required_libraries: list[str] = Field(default_factory=list)


class ExecutionFuture(BaseModel):
    execution_id: str
    status: ExecutionStatus = ExecutionStatus.QUEUED
    stream_url: str | None = None
    estimated_completion: float = 0.0
