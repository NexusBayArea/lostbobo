from __future__ import annotations

from pydantic import BaseModel


class KernelEvent(BaseModel):
    event_id: str
    event_type: str
    tenant_id: str
    timestamp: float
    payload: dict
    lineage_id: str | None = None
