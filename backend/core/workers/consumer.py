"""Redis Consumer Workers — background execution for Beam Orchestrator."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid

import redis.asyncio as redis

from backend.core.agents.orchestrator import AgentOrchestrator
from backend.core.orchestrator.beam_orchestrator import BeamOrchestrator
from backend.core.redis.beam_streamer import BeamStreamer
from backend.core.skills.registry import SkillRegistry
from backend.runtime.rag.router import RAGRouter

log = logging.getLogger(__name__)


class BeamWorker:
    def __init__(self, worker_id: str | None = None):
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        self.redis_client: redis.Redis | None = None
        self.streamer = BeamStreamer()
        self.skills = SkillRegistry()
        self.agents = AgentOrchestrator()
        self.beam_orch = BeamOrchestrator(agents=[], rag=RAGRouter(), config={})

    async def start(self):
        await self.streamer.connect()
        log.info("Worker %s started", self.worker_id)

        stages = ["plausibility", "rag", "simulation", "robustness"]
        for stage in stages:
            asyncio.create_task(self._consume_stage(stage))

        await asyncio.Future()

    async def _consume_stage(self, stage: str):
        stream_key = f"simhpc:prod:queue:{stage}"
        group = "beam_workers"
        consumer = self.worker_id

        try:
            await self.streamer.client.xgroup_create(stream_key, group, id="0", mkstream=True)
        except Exception:
            pass

        while True:
            try:
                messages = await self.streamer.client.xreadgroup(
                    group, consumer, streams={stream_key: ">"}, count=1, block=2000
                )
                if not messages:
                    continue

                for _stream, entries in messages:
                    for entry_id, data in entries:
                        payload = json.loads(data.get("data", "{}"))
                        hyp_id = payload.get("hypothesis_id")
                        request_id = payload.get("request_id")

                        log.info("[%s] Worker %s processing %s", stage, self.worker_id, hyp_id)

                        await self._execute_stage(stage, hyp_id, request_id)

                        await self.streamer.client.xack(stream_key, group, entry_id)

            except Exception as e:
                log.error("Worker error in %s: %s", stage, e)
                await asyncio.sleep(1)

    async def _execute_stage(self, stage: str, hyp_id: str, request_id: str):
        return await self.beam_orch.run("background-stage", tenant_id="public")
