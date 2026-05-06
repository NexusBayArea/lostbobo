"""Research Memory — persistent experiment ledger (Kernel-owned)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from backend.core.kernel.kernel import Kernel


@dataclass
class ExperimentRecord:
    id: str
    timestamp: datetime
    target: str
    change: dict[str, Any]
    result: dict[str, Any]
    accepted: bool
    experiment_id: str


class ResearchMemory:
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.experiments: dict[str, ExperimentRecord] = {}

    async def log(self, record: ExperimentRecord):
        self.experiments[record.id] = record
        await self.kernel.execute(
            {
                "type": "MEMORY_RECORD",
                "payload": {
                    "type": "experiment",
                    "content": {
                        "id": record.id,
                        "target": record.target,
                        "change": record.change,
                        "result": record.result,
                        "accepted": record.accepted,
                    },
                },
            }
        )

    async def get_best(self, target: str) -> ExperimentRecord | None:
        candidates = [r for r in self.experiments.values() if r.target == target and r.accepted]
        if not candidates:
            return None
        return max(candidates, key=lambda r: r.result.get("score", 0))
