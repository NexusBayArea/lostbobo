from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from backend.core.kernel.command_bus import command_bus
from backend.core.runtime.event_fabric.schema import SimHPCEvent
from backend.core.runtime.state_registry.service import StateRegistryService
from backend.core.services.observability_service import observability
from backend.core.tracing import trace_context


class PluginBase(ABC):
    """Official PluginRuntimeContract — enforced for all plugins."""

    name: str
    version: str = "0.1.0"
    enabled: bool = True

    async def initialize(self) -> None:
        """Called automatically by PluginRegistry on startup."""
        with trace_context("plugin.initialize", {"plugin": self.name}):
            registry = StateRegistryService.registry()
            registry.register_observer(self.observe)

            await command_bus.execute("PLUGIN_REGISTERED", plugin_name=self.name, version=self.version)

            observability().increment("plugins_initialized_total", tags={"plugin": self.name})

    @abstractmethod
    async def observe(self, state: Any) -> None:
        """
        React to live world state changes.
        This is the ONLY way plugins receive data from the runtime.
        """
        ...

    async def emit(
        self,
        event_type: str,
        payload: dict[str, Any],
        priority: str = "normal",
        confidence: float = 1.0,
    ) -> str:
        """
        The ONLY sanctioned way for a plugin to change the world.
        Returns the event_id.
        """
        with trace_context("plugin.emit", {"event_type": event_type, "plugin": self.name}):
            event = SimHPCEvent(
                event_type=event_type,
                source_plugin=self.name,
                priority=priority,
                confidence=confidence,
                payload=payload,
            )

            event_id = await command_bus.execute("EVENT_PUBLISH", event=event.model_dump())

            observability().increment("plugin_events_emitted_total", tags={"plugin": self.name})
            return event_id


# Convenience alias used in documentation and older references
PluginRuntimeContract = PluginBase
