"""Command Bus — routes every command through the Kernel."""

from __future__ import annotations

from typing import Any


class CommandBus:
    def __init__(self, kernel):
        self.kernel = kernel

    async def route(self, command: dict[str, Any]) -> Any:
        cmd_type = command["type"]
        payload = command.get("payload", {})

        if cmd_type == "MEMORY_RECORD":
            return await self.kernel.services["memory"].record(payload)
        if cmd_type == "MEMORY_QUERY":
            return await self.kernel.services["memory"].query(payload)
        if cmd_type == "MEMORY_RECONCILE":
            return await self.kernel.services["reconcile"].reconcile(payload["decision_id"], payload["observed"])
        if cmd_type == "WORLD_UPDATE":
            world_svc = self.kernel.services.get("world")
            return await world_svc.update(payload) if world_svc else {"status": "world_service_not_yet_wired"}
        if cmd_type == "SKILL_EXECUTE":
            return await self.kernel.skills.execute(payload["skill"], payload["input"])
        if cmd_type == "AGENT_RUN":
            agent_name = payload["agent"]
            return await self.kernel.agents[agent_name].run(payload["input"])
        raise ValueError(f"Unknown command type: {cmd_type}")
