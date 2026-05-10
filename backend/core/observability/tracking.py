from __future__ import annotations

import time
from typing import Any

from backend.app.core.supabase import get_supabase_client

from .forecasts import ForecastRecord


class ForecastTracker:
    """Central tracking engine — persists to Supabase."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._supabase = get_supabase_client()
        return cls._instance

    @classmethod
    def tracker(cls) -> ForecastTracker:
        return cls()

    async def track(self, record: ForecastRecord):
        """Track forecast — persisted as immutable record."""
        if self._supabase:
            self._supabase.table("forecast_records").insert(record.model_dump()).execute()

    async def resolve(self, forecast_id: str, actual_outcome: Any):
        """Mark forecast as resolved with ground truth."""
        if self._supabase:
            self._supabase.table("forecast_records").update(
                {
                    "actual_outcome": actual_outcome,
                    "resolved": True,
                    "resolved_at": time.time(),
                }
            ).eq("id", forecast_id).execute()
