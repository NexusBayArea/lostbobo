"""World state API — current state, replay, and SSE streaming."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from backend.core.runtime.entity_graph.service import EntityGraphService
from backend.core.runtime.state_registry.service import StateRegistryService

router = APIRouter(prefix="/world-state", tags=["WorldState"])


@router.get("/current")
async def get_current_state() -> dict[str, Any]:
    state = await StateRegistryService.registry().get_current()
    return state.model_dump(mode="json")


@router.get("/replay")
async def replay_state(at_ts: float = Query(..., description="Unix timestamp")) -> dict[str, Any]:
    state = await StateRegistryService.registry().reconstruct(at_ts)
    return state.model_dump(mode="json")


@router.get("/graph")
async def get_graph_snapshot(max_nodes: int = Query(default=200)) -> dict[str, Any]:
    return await EntityGraphService.graph().get_graph_snapshot(max_nodes=max_nodes)


@router.get("/stream")
async def stream_state() -> StreamingResponse:
    async def event_generator() -> AsyncIterator[bytes]:
        queue: asyncio.Queue[dict] = asyncio.Queue()

        async def on_state_update(state: Any) -> None:
            await queue.put(state.model_dump(mode="json"))

        registry = StateRegistryService.registry()
        await registry.observe(on_state_update)

        while True:
            try:
                state = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield f"data: {json.dumps(state)}\n\n"
            except TimeoutError:
                yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
