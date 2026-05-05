"""Redis-backed queue router for cascade orchestration."""

from __future__ import annotations

import json
import logging
import time

import redis.asyncio as redis

from backend.app.core.supabase import get_supabase_client

log = logging.getLogger(__name__)


class QueueRouter:
    """Central queue dispatcher. All heavy work goes through Redis → RunPod workers."""

    def __init__(self):
        self.redis = None
        self._sb = get_supabase_client()

    async def connect(self):
        if not self.redis:
            self.redis = redis.from_url("redis://localhost:6379", decode_responses=True)

    async def enqueue(self, stage: str, payload: dict) -> str:
        """Enqueue work for a specific stage. Returns job_id."""
        await self.connect()
        job_id = f"job:{stage}:{int(time.time()*1000)}"

        payload["job_id"] = job_id
        payload["stage"] = stage
        payload["enqueued_at"] = time.time()

        await self.redis.rpush(f"queue:{stage}", json.dumps(payload))
        await self.redis.hset(
            f"job:{job_id}",
            mapping={
                "status": "queued",
                "stage": stage,
                "payload": json.dumps(payload),
            },
        )

        log.info("Enqueued %s → %s", stage, job_id)
        return job_id

    async def get_next(self, stage: str) -> dict | None:
        """Worker pulls next job."""
        await self.connect()
        data = await self.redis.lpop(f"queue:{stage}")
        if not data:
            return None
        return json.loads(data)

    async def mark_complete(self, job_id: str, result: dict):
        """Worker calls this after completion."""
        await self.redis.hset(
            f"job:{job_id}",
            mapping={
                "status": "completed",
                "result": json.dumps(result),
                "completed_at": time.time(),
            },
        )
        if self._sb and "question_id" in result:
            try:
                self._sb.table("simulation_results").upsert(
                    {
                        "job_id": job_id,
                        **result,
                    }
                ).execute()
            except Exception as e:
                log.warning("Failed to persist result: %s", e)

    async def should_run_simulation(self, claim: dict) -> bool:
        """Skip simulation for low-confidence claims."""
        confidence = claim.get("confidence", 0.0)
        return confidence > 0.6

    async def should_run_robustness(self, sim_result: dict) -> bool:
        """Only run robustness if base simulation is marginal."""
        stability = sim_result.get("stability_score", 1.0)
        return stability < 0.85
