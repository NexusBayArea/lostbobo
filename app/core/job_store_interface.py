from typing import Any, Dict, Optional


class JobStoreInterface:
    async def insert_job(self, data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    async def get_job_by_idempotency(self, key: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    async def update_job(self, job_id: str, status: str, result: Optional[Dict] = None):
        raise NotImplementedError
