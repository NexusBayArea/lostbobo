from datetime import datetime

from app.models.event import JobEvent
from app.models.job import Job


def serialize_job(job: Job) -> str:
    """Serialize Job to JSON string."""
    return job.model_dump_json()


def deserialize_job(raw: str) -> Job:
    """Deserialize JSON string to Job."""
    if not raw:
        raise ValueError("Empty job data")
    return Job.model_validate_json(raw)


def serialize_event(event: JobEvent) -> str:
    """Serialize JobEvent to JSON string."""
    return event.model_dump_json()


def deserialize_event(raw: str) -> JobEvent:
    """Deserialize JSON string to JobEvent."""
    return JobEvent.model_validate_json(raw)


def now() -> datetime:
    """Get current UTC time."""
    return datetime.utcnow()


def job_to_dict(job: Job) -> dict:
    """Convert Job to dictionary for Supabase."""
    data = job.model_dump()
    # Convert datetime to ISO string for Supabase
    data["created_at"] = job.created_at.isoformat()
    data["updated_at"] = job.updated_at.isoformat()
    if job.completed_at:
        data["completed_at"] = job.completed_at.isoformat()
    return data
