"""SimHPC Kernel — Single Source of Truth."""

from __future__ import annotations

import logging
from typing import Any

from backend.core.kernel.agents.planner import PlannerAgent
from backend.core.kernel.auto_research.engine import AutoResearchEngine
from backend.core.kernel.command_bus import CommandBus
from backend.core.kernel.services.memory_service import KernelMemoryService
from backend.core.kernel.services.reconciliation_service import ReconciliationService
from backend.core.kernel.services.world_service import WorldService
from backend.core.kernel.skills.registry import SkillRegistry
from backend.core.kernel.state.memory_state import MemoryState
from backend.core.kernel.state.world_state import WorldState

log = logging.getLogger(__name__)


class Kernel:
    """Central orchestrator. All commands must go through here."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self.memory_state = MemoryState()
        self.world_state = WorldState()

        self.services = {
            "memory": KernelMemoryService(self.memory_state),
            "reconcile": ReconciliationService(self.memory_state),
            "world": WorldService(self.world_state),
        }

        self.skills = SkillRegistry()
        self.agents = {
            "planner": PlannerAgent(self),
        }
        self.auto_research = AutoResearchEngine(self)

        self.command_bus = CommandBus(self)

        log.info("SimHPC Kernel initialized — Single Source of Truth active")

    async def execute(self, command: dict[str, Any]) -> Any:
        """All execution paths go through here."""
        if not isinstance(command, dict) or "type" not in command:
            raise ValueError("Command must have 'type' field")

        log.debug("Kernel.execute → %s", command["type"])

        return await self.command_bus.route(command)

    async def _ensure_workers(self):
        """Background task to start Redis workers if not running."""
        from backend.core.workers.consumer import BeamWorker

        BeamWorker()
