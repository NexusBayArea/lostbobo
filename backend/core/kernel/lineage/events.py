# backend/core/kernel/lineage/events.py
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class LineageEvent:
    execution_id: str
    event_type: str
    source_type: str
    source_id: str
    payload: dict[str, Any]
    timestamp: datetime | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
