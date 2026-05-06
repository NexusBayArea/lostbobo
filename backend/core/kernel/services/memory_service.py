"""Kernel Memory Service — in-memory + persistent."""

from __future__ import annotations

from typing import Any

from backend.core.kernel.state.memory_state import MemoryState
from backend.core.memory.schema import MemoryRecord


class KernelMemoryService:
    def __init__(self, state: MemoryState):
        self.state = state

    async def record(self, payload: dict[str, Any]) -> MemoryRecord:
        record = MemoryRecord(
            id=payload.get("id", ""),
            type=payload.get("type", "observation"),
            timestamp=payload.get("timestamp"),
            context=payload.get("context", {}),
            content=payload.get("content", {}),
            outcome=payload.get("outcome", {}),
            links=payload.get("links", {"parent_ids": [], "child_ids": []}),
            tenant_id=payload.get("tenant_id", "public"),
        )
        return await self.state.store(record)

    async def query(self, payload: dict[str, Any]) -> list[MemoryRecord]:
        return await self.state.search(payload)
