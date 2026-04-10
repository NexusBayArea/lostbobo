import logging
import json
from typing import Optional
from redis import Redis
from pydantic import ValidationError

from app.models.job import Job
from app.models.version import CURRENT_JOB_SCHEMA_VERSION
from app.core.job_migrations import migrate_job

logger = logging.getLogger(__name__)


class ValidatedJobStore:
    """Strict schema validation at Redis boundary."""

    def __init__(self, redis: Redis):
        self.redis = redis

    def set_job(self, job: Job):
        """Validate schema BEFORE write to Redis."""
        try:
            job.schema_version = CURRENT_JOB_SCHEMA_VERSION
            validated = Job.model_validate(job.model_dump())
            self.redis.set(f"job:{validated.id}", validated.model_dump_json())
        except ValidationError as e:
            logger.error(
                "JOB_SCHEMA_VALIDATION_FAILED",
                extra={"job_id": getattr(job, "id", "unknown"), "errors": e.errors()},
            )
            raise

    def get_job(self, job_id: str) -> Optional[Job]:
        """Read and validate job from Redis."""
        raw = self.redis.get(f"job:{job_id}")
        if not raw:
            return None
        try:
            data = json.loads(raw)
            migrated = migrate_job(data)
            return Job.model_validate(migrated)
        except ValidationError as e:
            logger.critical(
                "JOB_SCHEMA_CORRUPTED_IN_REDIS",
                extra={"job_id": job_id, "errors": e.errors(), "raw": raw[:500]},
            )
            self.redis.set(f"corrupt:job:{job_id}", raw)
            self.redis.delete(f"job:{job_id}")
            return None
        except RuntimeError as e:
            logger.critical(
                "JOB_MIGRATION_FAILED",
                extra={"job_id": job_id, "error": str(e)},
            )
            return None

    def update_job(self, job_id: str, **updates) -> Job:
        """Safe update with validation."""
        job = self.get_job(job_id)
        if not job:
            raise RuntimeError(f"Job {job_id} not found or corrupted")
        updated_data = job.model_dump()
        updated_data.update(updates)
        updated_data["schema_version"] = CURRENT_JOB_SCHEMA_VERSION
        try:
            updated_job = Job.model_validate(updated_data)
        except ValidationError as e:
            logger.error(
                "JOB_UPDATE_VALIDATION_FAILED",
                extra={"job_id": job_id, "updates": updates, "errors": e.errors()},
            )
            raise
        self.redis.set(f"job:{job_id}", updated_job.model_dump_json())
        return updated_job

    def delete_job(self, job_id: str):
        """Delete job from Redis."""
        self.redis.delete(f"job:{job_id}")
        self.redis.delete(f"job:{job_id}:executed")
        self.redis.delete(f"job:{job_id}:executing")


_job_store = None


def init_job_store(redis: Redis) -> ValidatedJobStore:
    global _job_store
    _job_store = ValidatedJobStore(redis)
    return _job_store


def get_job_store() -> ValidatedJobStore:
    return _job_store
