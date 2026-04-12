from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from app.models.version import CURRENT_JOB_SCHEMA_VERSION
from packages.types.job import Job as SharedJob
from packages.types.enums import JobStatus

def generate_idempotency_key(payload: dict) -> str:
    """Generate deterministic idempotency key from job input params."""
    import hashlib
    import json

    normalized = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(normalized.encode()).hexdigest()[:32]


class JobProgress(BaseModel):
    percent: int = 0
    stage: Optional[str] = None
    current: Optional[int] = None
    total: Optional[int] = None


class JobResult(BaseModel):
    summary: Optional[str] = None
    output: Optional[Dict[str, Any]] = None


class Job(SharedJob):
    schema_version: int = CURRENT_JOB_SCHEMA_VERSION
    
    # Overriding fields to match existing app logic if needed
    input_params: Dict[str, Any] = {}
    scenario_name: Optional[str] = None
    idempotency_key: Optional[str] = None
    
    progress: JobProgress = JobProgress()
    
    # Redefine results to use JobResult model
    results: Optional[JobResult] = None # Using results instead of result for compatibility with some routes

    def generate_key(self) -> str:
        """Generate idempotency key from input params if not set."""
        if self.idempotency_key:
            return self.idempotency_key
        return generate_idempotency_key(self.input_params)

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> "Job":
        return cls(**data)
