"""
WebSocket Routes for Real-time Job Updates
Subscribes to Redis pub/sub and broadcasts to WebSocket clients
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import asyncio
import json
import os

router = APIRouter()

# Import existing connection manager from api.py
# Will be set via init_routes
manager = None
redis_client = None


def init_ws(redis_conn):
    global redis_client
    redis_client = redis_conn


class WSConnectionManager:
    """Manages WebSocket connections for job updates."""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)

    def disconnect(self, websocket: WebSocket, job_id: str):
        if job_id in self.active_connections:
            if websocket in self.active_connections[job_id]:
                self.active_connections[job_id].remove(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]

    async def send_to_job(self, job_id: str, message: dict):
        if job_id in self.active_connections:
            for connection in self.active_connections[job_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

    async def send_to_all(self, message: dict):
        for job_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass


ws_manager = WSConnectionManager()


@router.websocket("/ws/jobs/{job_id}")
async def websocket_job_updates(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for job-specific updates."""
    await ws_manager.connect(websocket, job_id)

    # Start Redis pub/sub listener for this job
    if redis_client:
        pubsub = redis_client.pubsub()
        await pubsub.subscribe("jobs:events")

        try:
            while True:
                message = await asyncio.wait_for(
                    pubsub.get_message(ignore_subscribe_messages=True, timeout=1),
                    timeout=5.0,
                )

                if message and message.get("type") == "message":
                    data = json.loads(message["data"])

                    # Only send relevant job updates
                    if data.get("data", {}).get("job_id") == job_id:
                        await websocket.send_json(data)

                # Keep connection alive with ping
                await asyncio.sleep(0.1)

        except asyncio.TimeoutError:
            pass
        except Exception:
            pass
        finally:
            await pubsub.unsubscribe("jobs:events")
            await pubsub.close()

    ws_manager.disconnect(websocket, job_id)


@router.websocket("/ws/all")
async def websocket_all_updates(websocket: WebSocket):
    """WebSocket endpoint for all job updates (admin/monitoring)."""
    await websocket.accept()

    if redis_client:
        pubsub = redis_client.pubsub()
        await pubsub.subscribe("jobs:events")

        try:
            while True:
                message = await asyncio.wait_for(
                    pubsub.get_message(ignore_subscribe_messages=True, timeout=1),
                    timeout=5.0,
                )

                if message and message.get("type") == "message":
                    await websocket.send_json(json.loads(message["data"]))

                await asyncio.sleep(0.1)

        except asyncio.TimeoutError:
            pass
        except Exception:
            pass
        finally:
            await pubsub.unsubscribe("jobs:events")
            await pubsub.close()
