"""Research Memory — persistent experiment ledger (Kernel-owned)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any   # List removed (unused)

from app.kernel.kernel import Kernel


@dataclass
class ExperimentRecord:
    id: str
    timestamp: datetime
    target: str                          # "compiler", "simulation", "policy"
    change: Dict[str, Any]
    result: Dict[str, Any]               # primary_metric, uncertainty, robustness
    accepted: bool
    experiment_id: str


class ResearchMemory:
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.experiments: Dict[str, ExperimentRecord] = {}

    async def log(self, record: ExperimentRecord):
        self.experiments[record.id] = record
        # Persist via Kernel → Memory Layer
        await self.kernel.execute({
            "type": "MEMORY_RECORD",
            "payload": {
                "type": "experiment",
                "content": record.__dict__
            }
        })

    async def get_best(self, target: str) -> ExperimentRecord | None:
        candidates = [r for r in self.experiments.values() if r.target == target and r.accepted]
        if not candidates:
            return None
        return max(candidates, key=lambda r: r.result.get("score", 0))


