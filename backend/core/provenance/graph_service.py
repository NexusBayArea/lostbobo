from __future__ import annotations

import logging
from typing import Any

from backend.app.core.supabase import get_supabase_client

log = logging.getLogger(__name__)


class HypothesisGraph:
    """Repository for managing Hypothesis Graph nodes in Supabase."""

    def __init__(self):
        self.client = get_supabase_client()

    async def add_hypothesis(self, data: dict[str, Any]) -> dict[str, Any]:
        """Insert a new hypothesis node."""
        if not self.client:
            return {}

        resp = await self.client.table("hypotheses").insert(data).execute()
        return resp.data[0] if resp.data else {}

    async def get_provenance(self, hyp_id: str) -> list[dict[str, Any]]:
        """Fetch provenance graph for a given hypothesis."""
        if not self.client:
            return []

        # Use the stored procedure defined in SQL
        resp = await self.client.rpc("get_hypothesis_provenance", {"hyp_id": hyp_id}).execute()
        return resp.data or []

    async def add_discovery(self, data: dict[str, Any]) -> dict[str, Any]:
        """Record a scientific discovery."""
        if not self.client:
            return {}

        resp = await self.client.table("discoveries").insert(data).execute()
        return resp.data[0] if resp.data else {}
