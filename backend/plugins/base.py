"""Base class for all SimHPC plugins."""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from backend.core.runtime.event_fabric.schema import SimHPCEvent
    from backend.core.world_model.schema import WorldState


class PluginBase(abc.ABC):
    """All domain plugins must inherit from this."""

    name: str
    version: str = "0.1.0"
    category: str = "domain"
    description: str = ""

    @abc.abstractmethod
    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Main execution entrypoint for the plugin."""
        ...

    async def validate_input(self, input_data: dict[str, Any]) -> bool:
        """Optional input validation hook."""
        return True

    async def get_metadata(self) -> dict[str, Any]:
        """Return plugin metadata for UI / registry."""
        return {
            "name": self.name,
            "version": self.version,
            "category": self.category,
            "description": self.description,
        }

    async def observe(self, state: WorldState) -> None:  # noqa: B027
        """React to world state changes via StateRegistry."""
        pass

    async def emit(self, event: SimHPCEvent) -> str:
        """Publish an event through the fabric (only way to change world state)."""
        from backend.core.kernel.command_bus import command_bus
        from backend.core.runtime.event_fabric.schema import SimHPCEvent

        evt = event if isinstance(event, SimHPCEvent) else SimHPCEvent.model_validate(event)
        return await command_bus.execute("EVENT_PUBLISH", payload={"event": evt.model_dump()})
