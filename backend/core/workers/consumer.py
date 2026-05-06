"""Redis Consumer Workers — background execution through Kernel only."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid

from backend.core.kernel.kernel import Kernel
from backend.core.redis.beam_streamer import BeamStreamer

log = logging.getLogger(__name__)


class BeamWorker:
    def __init__(self, worker_id: str | None = None):
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        self.streamer = BeamStreamer()
        self.kernel = Kernel()

    async def start(self):
        await self.streamer.connect()
        log.info("Worker %s started — all commands go through Kernel", self.worker_id)

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
                        request_id = payload.get("request_id")

                        log.info("[%s] Worker %s processing %s", stage, self.worker_id, request_id)

                        await self.kernel.execute(
                            {
                                "type": "AGENT_RUN",
                                "payload": {
                                    "agent": "planner",
                                    "input": {"stage": stage, "request_id": request_id, **payload},
                                },
                            }
                        )

                        await self.streamer.client.xack(stream_key, group, entry_id)

            except Exception as e:
                log.error("Worker %s error in %s: %s", self.worker_id, stage, e)
                await asyncio.sleep(1)
