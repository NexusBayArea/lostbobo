# backend/runtime/rag/dataset_index.py
from backend.app.core.supabase import get_supabase_client

from .base_index import BaseIndex


class DatasetIndex(BaseIndex):
    async def search(self, query: str, tenant_id: str = "public", limit: int = 8):
        sb = get_supabase_client()
        if not sb:
            return []
        try:
            resp = (
                sb.table("simulation_cache")
                .select("*")
                .eq("tenant_id", tenant_id)
                .eq("domain", self.domain)
                .text_search("query", query)
                .order("timestamp", desc=True)
                .limit(limit)
                .execute()
            )
            return resp.data or []
        except Exception as e:
            print(f"DatasetIndex error: {e}")
            return []
