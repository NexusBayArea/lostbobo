"""Command Bus — routes every command through the Kernel."""

from __future__ import annotations

from typing import Dict, Any


class CommandBus:
    def __init__(self, kernel):
        self.kernel = kernel

    async def route(self, command: Dict[str, Any]) -> Any:
        cmd_type = command["type"]
        payload = command.get("payload", {})

        match cmd_type:
            case "MEMORY_RECORD":
                return await self.kernel.services["memory"].record(payload)
            case "MEMORY_QUERY":
                return await self.kernel.services["memory"].query(payload)
            case "MEMORY_RECONCILE":
                return await self.kernel.services["reconcile"].reconcile(
                    payload["decision_id"], payload["observed"]
                )
            case "WORLD_UPDATE":
                return await self.kernel.services["world"].update(payload)
            case "SKILL_EXECUTE":
                return await self.kernel.skills.execute(
                    payload["skill"], payload["input"]
                )
            case "AGENT_RUN":
                agent_name = payload["agent"]
                return await self.kernel.agents[agent_name].run(payload["input"])
            case "BUILD_PROMPT":
                return await self.kernel.prompt_stack.build(
                    payload["agent_id"], payload["query"], payload.get("mode")
                )
            case "SAFEGUARD_GATE":
                return await self.kernel.safeguards.gate_action(payload)
            case "MONITOR_METRIC":
                return await self.kernel.safeguards.monitor_metric(payload["name"], payload["value"])
            case _:
                # Fallback
                return await self.kernel.execute(command)
