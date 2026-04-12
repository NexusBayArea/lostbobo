from pydantic import BaseModel, Field
from typing import Literal, Optional, Any
from datetime import datetime
from packages.types.enums import JobStatus

class Job(BaseModel):
    id: str
    user_id: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)
    status: JobStatus = JobStatus.QUEUED
    priority: int = 0
    tier: str = "free"
    fingerprint: Optional[str] = None
    
    workflow_id: Optional[str] = None
    
    lease_id: Optional[str] = None
    lease_expires_at: Optional[datetime] = None

    attempt_count: int = 0
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
