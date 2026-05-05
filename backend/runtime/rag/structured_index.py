from backend.app.core.supabase import get_supabase_client


class StructuredIndex:
    async def search(self, query: str, tenant_id: str = "public", limit: int = 8):
        sb = get_supabase_client()
        if not sb:
            return []
        try:
            resp = (
                sb.table("material_properties")
                .select("*")
                .eq("tenant_id", tenant_id)
                .text_search("property", query)
                .limit(limit)
                .execute()
            )
            return resp.data or []
        except Exception as e:
            print("StructuredIndex error:", e)
            return []
