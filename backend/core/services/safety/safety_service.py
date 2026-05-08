from typing import Any

import structlog

from backend.core.supabase_job_store import SupabaseJobStore
from backend.kernel.kernel import Kernel
from backend.runtime.safety.budget_manager import RetryBudgetManager
from backend.runtime.safety.execution_graph import ExecutionGraphEngine, SafetyCheckResult
from backend.runtime.safety.memory_trust import MemoryTrustWeights
from backend.runtime.safety.state_hash import StateHasher

log = structlog.get_logger(__name__)


class SafetyService:
    """Kernel-centered AI Loop Prevention & Runtime Stability Service."""

    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.supabase = SupabaseJobStore()

        self.execution_graph = ExecutionGraphEngine(kernel)
        self.state_hasher = StateHasher()
        self.budget_manager = RetryBudgetManager(kernel)
        self.memory_trust = MemoryTrustWeights(kernel)

    async def check_execution(self, payload: dict[str, Any]) -> SafetyCheckResult:
        """Central safety gate."""
        job_id = payload.get("job_id")
        current_state = payload.get("state") or {}

        # 1. State Hashing
        state_hash = self.state_hasher.hash(current_state)
        if await self.execution_graph.has_cycle_or_repeat(state_hash, job_id):
            await self.supabase.record_event(
                "loop_detected", {"job_id": job_id, "state_hash": state_hash, "type": "state_repeat"}
            )
            return SafetyCheckResult(safe=False, reason="State repeat / loop detected", action="HALT")

        # 2. Execution Graph
        graph_result = await self.execution_graph.check(payload)
        if not graph_result.safe:
            return graph_result

        # 3. Budget Enforcement
        budget_result = await self.budget_manager.check(payload)
        if not budget_result.safe:
            return budget_result

        # 4. Memory Trust
        await self.memory_trust.validate_write(payload)

        # 5. Convergence Check (stub)
        if payload.get("is_reflection_step"):
            # Convergence logic would go here
            pass

        await self.execution_graph.record_node(payload, state_hash)

        return SafetyCheckResult(safe=True, reason="All checks passed", action="CONTINUE")
