from __future__ import annotations

from pydantic import BaseModel


class LineageContract(BaseModel):
    lineage_id: str
    execution_id: str
    parent_lineage_id: str | None = None
    timestamp: float
    metadata: dict
