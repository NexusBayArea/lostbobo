"""Structured Index — Layer 2: Parameters, constants, equations."""

from __future__ import annotations

import logging
from typing import Any

from backend.app.core.supabase import get_supabase_client

log = logging.getLogger(__name__)


class StructuredIndex:
    async def search(
        self, query: str, tenant_id: str = "public", limit: int = 8
    ) -> list[dict[str, Any]]:
        """Search material properties and constants."""
        sb = get_supabase_client()
        if not sb:
            return []

        try:
            resp = sb.table("material_properties").select("*").eq("tenant_id", tenant_id).execute()
            return resp.data[:limit] if resp.data else []
        except Exception as e:
            log.warning("StructuredIndex search failed: %s", e)
            return []