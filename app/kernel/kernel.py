"""Kernel - core system orchestrating cognitive cycles."""

from __future__ import annotations

import logging
from typing import Dict, Any

from app.kernel.prompt.stack import PromptStack

log = logging.getLogger(__name__)


class Kernel:
    def __init__(self):
        self.prompt_stack = PromptStack(self)
        # Initialize mock services and skills for command bus compatibility
        self.services = {
            "memory": MemoryServiceMock(),
            "reconcile": ReconcileServiceMock(),
            "world": WorldServiceMock(),
        }
        self.skills = SkillsMock()
        self.agents = {"planner": PlannerAgentMock()}
        # Initialize safeguards service
        self.safeguards = SafeguardsService(self)
        # In a real system, you would initialize other subsystems here: memory, world model, etc.
        log.info("Kernel initialized")

    async def execute(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a command via the Kernel's command bus."""
        # This is a simplified version. In practice, this would route to appropriate handlers.
        command_type = command.get("type")
        payload = command.get("payload", {})

        if command_type == "BUILD_PROMPT":
            return await self.prompt_stack.build(
                payload["agent_id"], payload["query"], payload.get("mode")
            )
        elif command_type == "WORLD_UPDATE":
            # Return a mock world state for now
            return {
                "entities": {
                    "grid_load": "normal",
                    "weather": "clear",
                    "time": "2026-05-06T01:35:00Z",
                }
            }
        elif command_type == "MEMORY_QUERY":
            # Return mock memory observations
            observation_type = payload.get("type", "observation")
            limit = payload.get("limit", 5)
            return [
                {
                    "insight": f"Observation {i + 1}: System stable",
                    "type": observation_type,
                }
                for i in range(min(limit, 3))
            ]
        elif command_type == "SKILL_LIST":
            return list(self.skills.skills.keys())
        else:
            log.info(f"Executing command: {command_type}")
            return {"status": "ok", "command_type": command_type, "payload": payload}


# Mock classes for services and skills to make the command bus work
class MemoryServiceMock:
    async def record(self, payload):
        return {"status": "recorded", "payload": payload}

    async def query(self, payload):
        observation_type = payload.get("type", "observation")
        limit = payload.get("limit", 5)
        return [
            {
                "insight": f"Observation {i + 1}: System stable",
                "type": observation_type,
            }
            for i in range(min(limit, 3))
        ]


class ReconcileServiceMock:
    async def reconcile(self, decision_id, observed):
        return {"status": "reconciled", "decision_id": decision_id}


class WorldServiceMock:
    async def update(self, payload):
        return {
            "entities": {
                "grid_load": "normal",
                "weather": "clear",
                "time": "2026-05-06T01:35:00Z",
                **payload,
            }
        }


class SkillsMock:
    def __init__(self):
        self.skills = {
            "analysis": lambda x: {"result": "analyzed"},
            "build": lambda x: {"result": "built"},
            "optimize": lambda x: {"result": "optimized"},
            "execute": lambda x: {"result": "executed"},
        }

    async def execute(self, skill_name, input_data):
        if skill_name in self.skills:
            return {
                "status": "skill_executed",
                "skill": skill_name,
                "result": self.skills[skill_name](input_data),
            }
        return {"status": "skill_not_found", "skill": skill_name}


class PlannerAgentMock:
    async def run(self, input_data):
        return {"status": "agent_executed", "agent": "planner", "result": "planned"}
