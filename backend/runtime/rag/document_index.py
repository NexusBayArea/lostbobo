# backend/runtime/rag/document_index.py
from backend.app.core.supabase import get_supabase_client

from .base_index import BaseIndex


class DocumentIndex(BaseIndex):
    async def search(self, query: str, tenant_id: str = "public", limit: int = 8):
        sb = get_supabase_client()
        if not sb:
            return []
        try:
            resp = sb.rpc(
                "match_chunks",
                {
                    "query_embedding": await self._embed(query),
                    "match_count": limit,
                    "filter_tenant": tenant_id,
                    "filter_domain": self.domain,
                },
            ).execute()
            return resp.data or []
        except Exception as e:
            print(f"DocumentIndex error: {e}")
            return []

    async def _embed(self, text: str):
        return [0.0] * 1536  # Replace with real embedding
