from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class JobEvent(BaseModel):
    type: str  # job_started | job_progress | job_completed | job_failed | job_retrying | job_queued
    job_id: str
    user_id: Optional[str] = None

    status: Optional[str] = None
    progress: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retries: Optional[int] = None

    timestamp: datetime

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> "JobEvent":
        return cls(**data)
