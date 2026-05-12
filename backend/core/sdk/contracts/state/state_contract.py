from __future__ import annotations

from pydantic import BaseModel


class StateSnapshotContract(BaseModel):
    """
    FROZEN world state snapshot reference v1.0.0.
    """

    snapshot_id: str
    state_hash: str
    timestamp: float
    tenant_id: str
    data: dict
