from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from app.models.version import CURRENT_JOB_SCHEMA_VERSION


class JobProgress(BaseModel):
    percent: int = 0
    stage: Optional[str] = None
    current: Optional[int] = None
    total: Optional[int] = None


class JobResult(BaseModel):
    summary: Optional[str] = None
    output: Optional[Dict[str, Any]] = None


class Job(BaseModel):
    schema_version: int = CURRENT_JOB_SCHEMA_VERSION

    id: str
    user_id: str

    status: str = (
        "queued"  # queued | running | completed | failed | retrying | cancelled
    )
    progress: JobProgress = JobProgress()

    input_params: Dict[str, Any] = {}
    scenario_name: Optional[str] = None

    result: Optional[JobResult] = None
    error: Optional[str] = None

    retries: int = 0

    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> "Job":
        return cls(**data)
