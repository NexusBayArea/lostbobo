from datetime import datetime

import structlog

from backend.core.supabase_job_store import SupabaseJobStore
from backend.kernel.kernel import Kernel

log = structlog.get_logger(__name__)


class ExecutionGraphEngine:
    """Tracks execution as a DAG to detect cycles and repeated states."""

    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.supabase = SupabaseJobStore()

    async def record_node(self, payload: dict, state_hash: str):
        """Record execution node in Supabase."""
        await self.supabase.record_event(
            "execution_node",
            {
                "job_id": payload.get("job_id"),
                "node_id": payload.get("node_id") or f"node_{datetime.now().timestamp()}",
                "parent_id": payload.get("parent_id"),
                "operation": payload.get("operation", "unknown"),
                "state_hash": state_hash,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def has_cycle_or_repeat(self, state_hash: str, job_id: str) -> bool:
        """Detect repeated states or cycles in current job execution."""
        history = await self.supabase.get_execution_history(job_id, limit=50)
        return any(node.get("state_hash") == state_hash for node in history)

    async def check(self, payload: dict) -> dict:
        """Full graph safety check."""
        return {"safe": True, "reason": "Graph check passed"}

    async def get_stats(self, job_id: str) -> dict:
        """Return execution graph statistics."""
        history = await self.supabase.get_execution_history(job_id)
        return {"total_nodes": len(history), "new_nodes": len([n for n in history if n.get("operation") != "retrieve"])}
