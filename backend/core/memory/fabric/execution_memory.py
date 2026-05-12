from __future__ import annotations

from typing import Any

from pydantic import Field

from backend.core.memory.fabric.memory_types import BaseMemoryRecord, MemoryType


class ExecutionMemoryRecord(BaseMemoryRecord):
    dag_id: str | None = None
    node_id: str | None = None
    execution_state: dict[str, Any] = Field(default_factory=dict)

    def __init__(self, **data):
        data.setdefault("memory_type", MemoryType.EXECUTION)
        super().__init__(**data)
