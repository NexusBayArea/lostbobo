"""Base class for all SimHPC plugins."""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from backend.core.world_model.schema import WorldState


class PluginBase(abc.ABC):
    name: str
    version: str = "0.1.0"
    enabled: bool = True

    async def initialize(self) -> None:
        from backend.core.kernel.command_bus import command_bus
        from backend.core.runtime.state_registry.service import StateRegistryService

        registry = StateRegistryService.registry()
        registry.register_observer(self.observe)
        try:
            await command_bus.execute("PLUGIN_REGISTERED", plugin_name=self.name)
        except Exception:
            pass

    @abc.abstractmethod
    async def observe(self, state: WorldState) -> None:  # noqa: B027
        """React to world state changes — NO direct writes."""
        pass

    async def emit(
        self,
        event_type: str,
        payload: dict[str, Any],
        priority: str = "normal",
        confidence: float = 1.0,
    ) -> str:
        from backend.core.kernel.command_bus import command_bus
        from backend.core.runtime.event_fabric.schema import EventPriority, SimHPCEvent

        p = EventPriority(priority) if priority in ["critical", "high", "normal"] else EventPriority.NORMAL
        event = SimHPCEvent(
            event_type=event_type,
            source_plugin=self.name,
            priority=p,
            confidence=confidence,
            payload=payload,
        )
        return await command_bus.execute("EVENT_PUBLISH", payload={"event": event.model_dump()})
