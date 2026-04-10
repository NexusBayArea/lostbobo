import json
from typing import Dict, Set
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()
        if job_id not in self.connections:
            self.connections[job_id] = set()
        self.connections[job_id].add(websocket)

    def disconnect(self, websocket: WebSocket, job_id: str):
        if job_id in self.connections:
            self.connections[job_id].discard(websocket)
            if not self.connections[job_id]:
                del self.connections[job_id]

    async def broadcast(self, job_id: str, message: dict):
        if job_id not in self.connections:
            return

        dead = []
        for ws in self.connections[job_id]:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.disconnect(ws, job_id)


manager = ConnectionManager()
