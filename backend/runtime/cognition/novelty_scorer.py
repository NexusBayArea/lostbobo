from typing import Any

import numpy as np
import structlog

from backend.core.supabase_job_store import SupabaseJobStore
from backend.kernel.kernel import Kernel

log = structlog.get_logger(__name__)


class NoveltyScorer:
    """Measures semantic + structural novelty to detect stagnation / loops."""

    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.supabase = SupabaseJobStore()

    async def compute(self, payload: dict[str, Any]) -> float:
        """Returns novelty score in [0.0, 1.0]. Low score = likely loop / stagnation."""
        agent_results = payload["agent_results"]
        job_id = payload["job_id"]

        # 1. Semantic novelty (mocked embedding distance)
        current_embedding = np.random.rand(128)  # Mock
        previous_states = await self.supabase.get_previous_cognition_embeddings(job_id, limit=10)

        if previous_states:
            distances = [np.dot(current_embedding, prev) for prev in previous_states]
            semantic_novelty = 1.0 - max(distances) if distances else 1.0
        else:
            semantic_novelty = 1.0

        # 2. Structural novelty (graph branching)
        graph_stats = await self.kernel.services["execution_graph"].get_stats(job_id)
        structural_novelty = min(1.0, graph_stats.get("new_nodes", 1) / max(graph_stats.get("total_nodes", 1), 1))

        # 3. Trust-weighted information gain
        trust_scores = [r.get("trust_score", 0.0) for r in agent_results.values()]
        trust_gain = sum(trust_scores) / max(len(trust_scores), 1)

        # Combined novelty score
        novelty_score = semantic_novelty * 0.5 + structural_novelty * 0.3 + trust_gain * 0.2

        await self.supabase.record_event(
            "novelty_scored",
            {
                "job_id": job_id,
                "novelty_score": novelty_score,
                "semantic": semantic_novelty,
                "structural": structural_novelty,
            },
        )

        log.info("novelty scored", score=novelty_score, job_id=job_id)
        return float(novelty_score)
