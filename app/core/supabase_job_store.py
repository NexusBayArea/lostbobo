from typing import Any, Dict, Optional

from app.core.job_store_interface import JobStoreInterface


class SupabaseJobStore(JobStoreInterface):
    def __init__(self, client):
        self.client = client

    async def insert_job(self, data: Dict[str, Any]) -> Dict[str, Any]:
        res = self.client.table("jobs").insert(data).execute()
        return res.data[0]

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        res = self.client.table("jobs").select("*").eq("id", job_id).single().execute()
        return res.data[0] if res.data else None

    async def get_job_by_idempotency(self, key: str) -> Optional[Dict[str, Any]]:
        res = (
            self.client.table("jobs")
            .select("*")
            .eq("idempotency_key", key)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    async def update_job(self, job_id: str, status: str, result: Optional[Dict] = None):
        payload = {"status": status}
        if result:
            payload["result"] = result

        res = self.client.table("jobs").update(payload).eq("id", job_id).execute()
        return res.data[0] if res.data else None
