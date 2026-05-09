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
        if cmd_type == "AUTO_RESEARCH_RUN":
            return await self.kernel.auto_research.run_research_cycle(payload["target"], payload["dsl"])
        if cmd_type == "OBSERVE_EVENT":
            return await self.kernel.observer.observe(payload["event"])
        if cmd_type == "REFLECT":
            return await self.kernel.reflector.reflect(payload["observations"])
        if cmd_type == "DEPTH_STORE":
            return await self.kernel.depth_registry.store(payload["layer"], payload["state"], payload.get("metadata"))
        if cmd_type == "DEPTH_QUERY":
            return await self.kernel.depth_registry.query(payload["query"], payload.get("top_k", 8))
        if cmd_type == "EVENT_PUBLISH":
            from backend.core.runtime.event_fabric.log import EventLogService

            event = EventLogService.event_log()
            evt = payload["event"]
            from backend.core.runtime.event_fabric.schema import SimHPCEvent

            sim_event = SimHPCEvent.model_validate(evt)
            return await event.publish(sim_event)
        if cmd_type == "EVENT_SUBSCRIBE":
            from backend.core.runtime.event_fabric.log import EventLogService

            EventLogService.event_log().subscribe(payload["pattern"], payload["handler"])
            return {"status": "subscribed"}
        if cmd_type == "STATE_MUTATE":
            from backend.core.runtime.event_fabric.schema import SimHPCEvent
            from backend.core.runtime.state_registry.service import StateRegistryService

            evt = SimHPCEvent.model_validate(payload["event"])
            return await StateRegistryService.registry().mutate(evt)
        raise ValueError(f"Unknown command type: {cmd_type}")
