from backend.app.core.supabase import get_supabase_client
from backend.runtime.rag.utils import embed_text

class DocumentIndex:
    async def search(self, query: str, tenant_id: str = "public", limit: int = 8):
        sb = get_supabase_client()
        if not sb:
            return []

        try:
            # Uses your existing match_chunks RPC with tenant filter
            resp = sb.rpc("match_chunks", {
                "query_embedding": await embed_text(query),
                "match_count": limit,
                "filter_tenant": tenant_id
            }).execute()
            return resp.data or []
        except Exception as e:
            print("DocumentIndex error:", e)
            return []
