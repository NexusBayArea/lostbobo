"""
WebSocket Routes for Real-time Job Updates
Subscribes to Redis pub/sub and broadcasts to WebSocket clients
"""

from fastapi import APIRouter, WebSocket, status
from typing import Dict, List
import asyncio
import json

router = APIRouter()

manager = None
redis_client = None
verify_auth = None

# Import unified guards
from app.core.guards import get_guards, GuardContext


def init_ws(redis_conn, auth_dep):
    global redis_client, verify_auth
    redis_client = redis_conn
    verify_auth = auth_dep


async def verify_ws_auth(websocket: WebSocket) -> dict:
    """Extract and verify JWT from WebSocket connection."""
    guards = get_guards()
    return await guards.authenticate_ws(websocket, verify_auth)


def user_owns_job(job_id: str, user_id: str) -> bool:
    """Verify user owns the job."""
    guards = get_guards()
    ctx = GuardContext({"user_id": user_id}, job_id)
    try:
        guards.assert_job_ownership(ctx)
        return True
    except:
        return False


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
    """WebSocket endpoint for job-specific updates with auth."""
    # 1. Authenticate
    try:
        user = await verify_ws_auth(websocket)
    except Exception:
        return  # Auth failed, connection closed

    user_id = user.get("user_id")

    # 2. Authorize (ownership check)
    if not user_owns_job(job_id, user_id) and user.get("type") != "api_key":
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # 3. Accept connection
    await ws_manager.connect(websocket, job_id)

    # 4. Send initial state (removes UI race condition)
    if redis_client:
        job_raw = redis_client.get(f"job:{job_id}")
        if job_raw:
            try:
                await websocket.send_text(job_raw)
            except Exception:
                pass

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
