"""In-memory + persistent state for Memory Layer (Kernel-owned)."""

from __future__ import annotations

from typing import Any

from backend.core.memory.schema import MemoryRecord


class MemoryState:
    def __init__(self):
        self.records: dict[str, MemoryRecord] = {}

    async def store(self, record: MemoryRecord):
        self.records[record.id] = record
        return record

    async def get(self, record_id: str) -> MemoryRecord | None:
        return self.records.get(record_id)

    async def search(self, filters: dict[str, Any]) -> list[MemoryRecord]:
        results = list(self.records.values())
        if "type" in filters:
            results = [r for r in results if r.type == filters["type"]]
        return results
