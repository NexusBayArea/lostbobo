"""Auto-Research Engine — closed-loop optimization (Kernel-managed)."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from backend.core.kernel.auto_research.evaluation import compute_score, run_simulation_gate
from backend.core.kernel.auto_research.memory import ExperimentRecord, ResearchMemory
from backend.core.kernel.kernel import Kernel

log = logging.getLogger(__name__)


class AutoResearchEngine:
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.memory = ResearchMemory(kernel)

    async def run_research_cycle(self, target: str, research_dsl: dict[str, Any]) -> dict[str, Any]:
        """One full auto-research iteration."""
        experiment_id = f"exp_{int(datetime.utcnow().timestamp()*1000)}"

        proposed_change = await self._propose_change(research_dsl)

        experiment_result = await self.kernel.execute(
            {
                "type": "SKILL_EXECUTE",
                "payload": {
                    "skill": research_dsl.get("skill"),
                    "input": proposed_change,
                },
            }
        )

        score = compute_score(experiment_result)
        accepted = run_simulation_gate(experiment_result) and score > research_dsl.get("baseline_score", 0)

        record = ExperimentRecord(
            id=experiment_id,
            timestamp=datetime.utcnow(),
            target=target,
            change=proposed_change,
            result={**experiment_result, "score": score},
            accepted=accepted,
            experiment_id=experiment_id,
        )
        await self.memory.log(record)

        log.info("Auto-research cycle complete → %s | score=%.3f | accepted=%s", target, score, accepted)

        return {
            "experiment_id": experiment_id,
            "accepted": accepted,
            "score": score,
            "change": proposed_change,
            "result": experiment_result,
        }

    async def _propose_change(self, research_dsl: dict[str, Any]) -> dict[str, Any]:
        """Controlled mutation within DSL-defined search space."""
        return {
            "parameter": "batch_size",
            "value": 64,
            "reason": "auto-research proposal",
        }
