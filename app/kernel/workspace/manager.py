"""Per-Agent Workspace — persistent cognitive state."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.kernel.kernel import Kernel

log = logging.getLogger(__name__)


@dataclass
class Workspace:
    agent_id: str
    memory_snapshot: Dict[str, Any] = None
    skills: List[str] = None
    experiments: List[Dict] = None
    artifacts: Dict[str, Any] = None
    mode: str = "analysis"  # analysis | build | optimize | execute
    last_updated: datetime = None

    def __post_init__(self):
        if self.skills is None:
            self.skills = []
        if self.experiments is None:
            self.experiments = []
        if self.artifacts is None:
            self.artifacts = {}
        if self.last_updated is None:
            self.last_updated = datetime.utcnow()


class WorkspaceManager:
    def __init__(self, kernel: "Kernel"):
        self.kernel = kernel
        self.workspaces: Dict[str, Workspace] = {}

    async def get_or_create(self, agent_id: str) -> Workspace:
        if agent_id not in self.workspaces:
            ws = Workspace(agent_id=agent_id)
            self.workspaces[agent_id] = ws
            # Persist initial workspace via Kernel
            await self.kernel.execute({
                "type": "MEMORY_RECORD",
                "payload": {
                    "type": "workspace_init",
                    "content": {"agent_id": agent_id, "mode": ws.mode}
                }
            })
        return self.workspaces[agent_id]

    async def update(self, agent_id: str, updates: Dict[str, Any]):
        ws = await self.get_or_create(agent_id)
        for key, value in updates.items():
            if hasattr(ws, key):
                setattr(ws, key, value)
        ws.last_updated = datetime.utcnow()

        await self.kernel.execute({
            "type": "MEMORY_RECORD",
            "payload": {
                "type": "workspace_update",
                "content": {"agent_id": agent_id, **updates}
            }
        })
        return ws