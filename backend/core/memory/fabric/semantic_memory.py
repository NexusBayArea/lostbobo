from __future__ import annotations

from pydantic import Field

from backend.core.memory.fabric.memory_types import BaseMemoryRecord, MemoryType


class SemanticMemoryRecord(BaseMemoryRecord):
    text: str
    embedding: list[float] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)

    def __init__(self, **data):
        data.setdefault("memory_type", MemoryType.SEMANTIC)
        super().__init__(**data)
