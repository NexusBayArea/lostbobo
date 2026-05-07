"""BeamStreamer — backed by SupabaseJobStore (Redis removed)."""

from __future__ import annotations

import logging
import time

from backend.core.models.hypothesis import Hypothesis
from backend.core.supabase_job_store import SupabaseJobStore

log = logging.getLogger(__name__)


class BeamStreamer:
    """Supabase-backed real-time beam state and streaming."""

    def __init__(self):
        self.store = SupabaseJobStore()
        self.env = "prod"

    async def connect(self):
        await self.store.connect()
        log.info("BeamStreamer connected (Supabase)")

    async def publish_hypothesis(self, hyp: Hypothesis, request_id: str):
        """Publish hypothesis update to beam channel."""
        await self.store.publish(
            f"beam:{request_id}",
            {
                "event": "beam_update",
                "timestamp": time.time(),
                "hypothesis_id": hyp.id,
                "trust_score": hyp.trust_score,
                "stage": hyp.stage,
                "agent_id": getattr(hyp, "agent_id", "unknown"),
            },
        )

    async def get_top_beams(self, request_id: str, count: int = 5):
        """Placeholder for beam retrieval (extend with query later)."""
        return []

    async def rerank_and_notify(self, request_id: str, beams: list[Hypothesis]):
        """Publish beam rerank event."""
        top_k = [{"id": h.id, "trust_score": h.trust_score} for h in beams[:3]]
        await self.store.publish(
            f"beam:{request_id}", {"event": "beam_reranked", "top_k": top_k, "timestamp": time.time()}
        )
