from __future__ import annotations

from pydantic import BaseModel


class KernelEvent(BaseModel):
    """
    FROZEN event schema v1.0.0.
    NEVER remove or rename fields; only add optional fields.
    """

    event_id: str
    event_type: str
    tenant_id: str
    timestamp: float
    payload: dict
    lineage_id: str | None = None
