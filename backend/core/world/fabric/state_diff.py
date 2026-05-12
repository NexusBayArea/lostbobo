from typing import Any

from pydantic import BaseModel


class StateDiff(BaseModel):
    diff_id: str
    snapshot_id: str
    changes: dict[str, Any]
    author_plugin: str
    timestamp: float
    parent_vector_clock: dict[str, int] = {}
    confidence: float = 1.0
