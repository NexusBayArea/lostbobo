from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from packages.types.enums import JobStatus


class Job(BaseModel):
    id: str
    user_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    status: JobStatus = JobStatus.QUEUED
    priority: int = 0
    tier: str = "free"
    fingerprint: str | None = None

    workflow_id: str | None = None

    lease_id: str | None = None
    lease_expires_at: datetime | None = None

    attempt_count: int = 0
    result: dict[str, Any] | None = None
    error: str | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None
    completed_at: datetime | None = None
