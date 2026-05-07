"""WebSocket Kill Switch — Emergency halt for running swarms."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.runtime.swarm.swarm_coordinator import SwarmCoordinator

log = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["kill-switch"])

active_swarms: dict[str, SwarmCoordinator] = {}
active_connections: dict[str, WebSocket] = {}


@router.websocket("/swarm")
async def swarm_kill_switch(websocket: WebSocket):
    """WebSocket endpoint for real-time kill switch."""
    await websocket.accept()
    market_id = "global"
    active_connections[market_id] = websocket

    try:
        while True:
            data = await websocket.receive_json()
            command = data.get("command")

            if command == "EMERGENCY_HALT":
                await handle_emergency_halt(data.get("market_id"), websocket)
            elif command == "STATUS":
                await websocket.send_json({"status": "connected", "active_swarms": list(active_swarms.keys())})
    except WebSocketDisconnect:
        active_connections.pop(market_id, None)
        log.info("WebSocket disconnected for market %s", market_id)


async def handle_emergency_halt(market_id: str, ws: WebSocket):
    """Emergency shutdown of running swarm."""
    log.critical("EMERGENCY HALT for market %s", market_id)

    if market_id in active_swarms:
        coordinator = active_swarms[market_id]
        await coordinator.abort_current_run()
        active_swarms.pop(market_id)

    await ws.send_json(
        {"event": "emergency_halt_executed", "market_id": market_id, "timestamp": asyncio.get_event_loop().time()}
    )

    for conn in active_connections.values():
        try:
            await conn.send_json({"event": "emergency_halt_broadcast", "market_id": market_id})
        except Exception:
            pass
