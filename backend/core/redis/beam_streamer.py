"""Redis Streaming Layer for Beam Orchestrator — Real-time Hypothesis updates."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import redis.asyncio as redis
from backend.core.models.hypothesis import Hypothesis

log = logging.getLogger(__name__)


class BeamStreamer:
    """Redis-backed real-time beam state and streaming."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.client: redis.Redis | None = None
        self.env = "prod"

    async def connect(self):
        if not self.client:
            self.client = redis.from_url(self.redis_url, decode_responses=True)
            await self.client.ping()
            log.info("Redis BeamStreamer connected")

    def _beam_key(self, request_id: str) -> str:
        return f"simhpc:{self.env}:beam:{request_id}"

    def _hyp_key(self, hyp_id: str) -> str:
        return f"simhpc:{self.env}:hypothesis:{hyp_id}"

    def _stream_key(self, request_id: str) -> str:
        return f"simhpc:{self.env}:stream:{request_id}"

    async def publish_hypothesis(self, hyp: Hypothesis, request_id: str):
        """Store hypothesis as HASH and add to beam ZSET."""
        await self.connect()

        hyp_data = {
            "claim": json.dumps(hyp.claim),
            "reasoning": hyp.reasoning,
            "sim_params": json.dumps(hyp.sim_params),
            "sim_result": json.dumps(hyp.sim_result) if hyp.sim_result else "{}",
            "plausibility_score": str(hyp.plausibility_score),
            "math_score": str(hyp.math_score),
            "simulation_score": str(hyp.simulation_score),
            "robustness_score": str(hyp.robustness_score),
            "rag_score": str(hyp.rag_score),
            "consensus_score": str(hyp.consensus_score),
            "trust_score": str(hyp.trust_score),
            "stage": hyp.stage,
            "agent_id": hyp.agent_id,
            "created_at": str(hyp.created_at),
        }

        await self.client.hset(self._hyp_key(hyp.id), mapping=hyp_data)
        await self.client.zadd(self._beam_key(request_id), {hyp.id: hyp.trust_score})

        await self._publish_event(
            request_id,
            {
                "event": "beam_update",
                "timestamp": time.time(),
                "hypothesis_id": hyp.id,
                "trust_score": hyp.trust_score,
                "stage": hyp.stage,
                "agent_id": hyp.agent_id,
            },
        )

    async def get_top_beams(self, request_id: str, count: int = 5) -> list[dict[str, Any]]:
        """Return top N hypotheses from ZSET."""
        await self.connect()
        members = await self.client.zrevrange(self._beam_key(request_id), 0, count - 1, withscores=True)
        return [{"id": m[0], "trust_score": m[1]} for m in members]

    async def _publish_event(self, request_id: str, payload: dict[str, Any]):
        """Stream real-time update to frontend."""
        await self.client.xadd(
            self._stream_key(request_id),
            {"data": json.dumps(payload)},
            maxlen=1000,
            approximate=True,
        )

    async def rerank_and_notify(self, request_id: str, beams: list[Hypothesis]):
        """Orchestrator-only ranking + broadcast."""
        pipeline = self.client.pipeline()
        for h in beams:
            pipeline.zadd(self._beam_key(request_id), {h.id: h.trust_score})
        await pipeline.execute()

        top = await self.get_top_beams(request_id, 3)
        await self._publish_event(
            request_id,
            {
                "event": "beam_reranked",
                "top_k": top,
                "timestamp": time.time(),
            },
        )
