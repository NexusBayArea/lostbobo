"""Document Index — Layer 1: Papers & unstructured."""

from __future__ import annotations

import logging
from typing import Any

from backend.app.core.supabase import get_supabase_client

log = logging.getLogger(__name__)


class DocumentIndex:
    async def search(
        self, query: str, tenant_id: str = "public", limit: int = 8
    ) -> list[dict[str, Any]]:
        """Search document chunks."""
        sb = get_supabase_client()
        if not sb:
            return []

        try:
            resp = sb.rpc("match_chunks", {
                "query_text": query,
                "match_count": limit,
                "filter_tenant": tenant_id,
            }).execute()
            return resp.data or []
        except Exception as e:
            log.warning("DocumentIndex search failed: %s", e)
            return []