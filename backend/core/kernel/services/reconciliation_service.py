"""Reconciliation Service — closes the learning loop."""

from __future__ import annotations

from typing import Any

from backend.core.kernel.state.memory_state import MemoryState


class ReconciliationService:
    def __init__(self, state: MemoryState):
        self.state = state

    async def reconcile(self, decision_id: str, observed: dict[str, Any]) -> dict[str, Any]:
        record = await self.state.get(decision_id)
        if not record:
            return {"error": "not found"}

        record.outcome["observed"] = observed
        record.outcome["error"] = abs(observed.get("value", 0) - record.content.get("expected", 0))
        await self.state.store(record)
        return {"decision_id": decision_id, "error": record.outcome["error"]}
