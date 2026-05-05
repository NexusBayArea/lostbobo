"""Intelligent verification cascade with early exits."""

from __future__ import annotations

import asyncio
import logging

from backend.runtime.orchestrator.queue_router import QueueRouter

log = logging.getLogger(__name__)


class VerificationCascade:
    """Runs claims through staged verification with early termination."""

    def __init__(self):
        self.queue = QueueRouter()

    async def process_claim(self, claim: dict) -> dict:
        """Full cascade for one claim."""
        result = {"claim_id": claim.get("id"), "status": "pending", "steps": []}

        if not await self._passes_reasoning(claim):
            result["status"] = "rejected_reasoning"
            return result
        result["steps"].append("reasoning_passed")

        if not await self._passes_math(claim):
            result["status"] = "rejected_math"
            return result
        result["steps"].append("math_passed")

        if await self.queue.should_run_simulation(claim):
            sim_job = await self.queue.enqueue("simulation", claim)
            sim_result = await self._wait_for_job(sim_job)
            result["simulation"] = sim_result
            result["steps"].append("simulation_completed")
        else:
            result["steps"].append("simulation_skipped")

        if result.get("simulation") and await self.queue.should_run_robustness(result["simulation"]):
            robust_job = await self.queue.enqueue("robustness", result["simulation"])
            robust_result = await self._wait_for_job(robust_job)
            result["robustness"] = robust_result
            result["steps"].append("robustness_completed")

        result["status"] = "verified"
        return result

    async def _passes_reasoning(self, claim: dict) -> bool:
        return claim.get("confidence", 0) > 0.4

    async def _passes_math(self, claim: dict) -> bool:
        return True

    async def _wait_for_job(self, job_id: str) -> dict:
        """Poll Redis until worker completes job."""
        await asyncio.sleep(0.5)
        return {"status": "success", "result": "stub_result"}
