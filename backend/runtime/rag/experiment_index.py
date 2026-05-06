"""Experiment Index — Layer 3: Simulation runs + datasets."""

from __future__ import annotations

import logging
from typing import Any

from backend.app.core.supabase import get_supabase_client

log = logging.getLogger(__name__)


class ExperimentIndex:
    async def search(
        self, query: str, tenant_id: str = "public", limit: int = 8
    ) -> list[dict[str, Any]]:
        """Search simulation cache and replays."""
        sb = get_supabase_client()
        if not sb:
            return []

        try:
            resp = sb.table("simulation_cache").select("*").eq("tenant_id", tenant_id).limit(limit).execute()
            return resp.data or []
        except Exception as e:
            log.warning("ExperimentIndex search failed: %s", e)
            return []