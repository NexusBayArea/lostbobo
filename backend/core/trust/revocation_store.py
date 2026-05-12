from __future__ import annotations

from backend.app.core.supabase import get_supabase_client


class RevocationStore:
    def __init__(self):
        self._supabase = get_supabase_client()
        self._cache: set[str] = set()

    async def is_revoked(self, plugin_id: str) -> bool:
        if plugin_id in self._cache:
            return True

        if self._supabase is None:
            return False

        try:
            result = (
                self._supabase.table("plugins")
                .select("revoked")
                .eq("plugin_id", plugin_id)
                .eq("revoked", True)
                .execute()
            )
            if result.data:
                self._cache.add(plugin_id)
                return True
        except Exception:
            pass

        return False

    async def refresh(self):
        self._cache.clear()
