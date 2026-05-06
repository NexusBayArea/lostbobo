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
            return await self.kernel.services["world"].update(payload)
        if cmd_type == "WORLD_SIMULATE":
            return await self.kernel.services["world"].simulate(payload)
        if cmd_type == "WORLD_PROPAGATE":
            return await self.kernel.services["world"].propagate_uncertainty(payload)
        if cmd_type == "SKILL_EXECUTE":
            return await self.kernel.skills.execute(payload["skill"], payload["input"])
        if cmd_type == "AGENT_RUN":
            agent_name = payload["agent"]
            return await self.kernel.agents[agent_name].run(payload["input"])
        raise ValueError(f"Unknown command type: {cmd_type}")
