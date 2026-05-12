from __future__ import annotations

from pydantic import BaseModel


class StateSnapshotContract(BaseModel):
    snapshot_id: str
    state_hash: str
    timestamp: float
    tenant_id: str
    data: dict
