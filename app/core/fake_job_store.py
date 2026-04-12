import uuid
from typing import Any, Dict, Optional

from app.core.job_store_interface import JobStoreInterface


class FakeJobStore(JobStoreInterface):
    def __init__(self):
        self.jobs = {}
        self.idempotency = {}

    async def insert_job(self, data: Dict[str, Any]) -> Dict[str, Any]:
        job_id = str(uuid.uuid4())[:8]
        job = {
            "id": job_id,
            "status": data.get("status", "queued"),
            "user_id": data.get("user_id"),
            "input_params": data.get("input_params", {}),
            "idempotency_key": data.get("idempotency_key"),
            "created_at": "2026-04-11T00:00:00Z",
            "updated_at": "2026-04-11T00:00:00Z",
            "completed_at": None,
            "result": None,
            "error": None,
        }
        self.jobs[job_id] = job

        if job.get("idempotency_key"):
            self.idempotency[job["idempotency_key"]] = job_id

        return job

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self.jobs.get(job_id)

    async def get_job_by_idempotency(self, key: str) -> Optional[Dict[str, Any]]:
        job_id = self.idempotency.get(key)
        if job_id:
            return self.jobs.get(job_id)
        return None

    async def update_job(self, job_id: str, status: str, result: Optional[Dict] = None):
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = status
            self.jobs[job_id]["updated_at"] = "2026-04-11T00:00:00Z"
            if result:
                self.jobs[job_id]["result"] = result
            if status == "completed":
                self.jobs[job_id]["completed_at"] = "2026-04-11T00:00:00Z"
            return self.jobs[job_id]
        return None

    async def get_last_job(self) -> Optional[Dict[str, Any]]:
        if self.jobs:
            return list(self.jobs.values())[-1]
        return None

    async def list_jobs(self, user_id: str, limit: int = 10) -> list[Dict[str, Any]]:
        return [job for job in self.jobs.values() if job.get("user_id") == user_id][
            :limit
        ]
