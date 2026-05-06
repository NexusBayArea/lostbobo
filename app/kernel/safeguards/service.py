"""Production Safeguards Service — action gating + quality filters."""

from __future__ import annotations

import logging
from typing import Dict, Any

from app.kernel.safeguards.drift import DriftDetector
from app.kernel.kernel import Kernel

log = logging.getLogger(__name__)


class SafeguardsService:
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.drift = DriftDetector(kernel)

    async def gate_action(self, action: Dict[str, Any]) -> bool:
        """Gate every potentially dangerous action."""
        if self.drift.quarantine:
            log.error("Action blocked: system in quarantine")
            return False

        # Require simulation validation for mutations
        if action.get("mutation", False):
            sim_result = await self.kernel.execute({
                "type": "WORLD_SIMULATE",
                "payload": action.get("simulation_input", {})
            })
            if not sim_result.get("passed_gate", False):
                log.warning("Action rejected by simulation gate")
                return False

        # Memory quality filter
        if "observation" in action:
            if action["observation"].get("confidence", 0) < 0.6:
                log.info("Low-confidence observation discarded")
                return False

        return True

    async def monitor_metric(self, name: str, value: float):
        """Continuous monitoring hook."""
        await self.drift.check(name, value)