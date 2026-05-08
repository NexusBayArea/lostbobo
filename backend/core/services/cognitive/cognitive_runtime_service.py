from typing import Any

import structlog

from backend.core.supabase_job_store import SupabaseJobStore
from backend.kernel.kernel import Kernel
from backend.runtime.cognition.cognitive_router import CognitiveRouter
from backend.runtime.cognition.execution_attention_graph import ExecutionAttentionGraph
from backend.runtime.cognition.multi_res_cognition import MultiResolutionCognition
from backend.runtime.cognition.novelty_scorer import NoveltyScorer

log = structlog.get_logger(__name__)


class CognitiveRuntimeService:
    """Central service for structured intermediate cognition."""

    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.supabase = SupabaseJobStore()

        self.execution_graph = ExecutionAttentionGraph(kernel)
        self.multi_res = MultiResolutionCognition(kernel)
        self.router = CognitiveRouter()
        self.novelty_scorer = NoveltyScorer(kernel)

    async def attend(self, query: str, job_id: str, top_k: int = 8) -> list[Any]:
        """Selective retrieval of relevant prior cognition states."""
        return await self.execution_graph.attend(query, job_id, top_k)

    async def route(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Sparse, multi-resolution cognitive routing."""
        return await self.router.route(payload)

    async def record_node(self, node_data: dict[str, Any], job_id: str):
        """Record structured cognition node."""
        await self.execution_graph.add_node(node_data, job_id)

    async def fuse_context(self, job_id: str) -> dict[str, Any]:
        """Get fused local + global cognition state."""
        local = await self.multi_res.get_local_state(job_id)
        global_state = await self.multi_res.get_global_state()
        return await self.multi_res.fuse_states(local, global_state)

    async def compute_novelty(self, payload: dict[str, Any]) -> float:
        """Entropy / novelty scoring."""
        return await self.novelty_scorer.compute(payload)
