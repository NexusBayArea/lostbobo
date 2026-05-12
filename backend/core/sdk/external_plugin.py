from __future__ import annotations

from abc import ABC, abstractmethod

from backend.core.sdk.runtime.plugin_context import PluginContext


class SimHPCPlugin(ABC):
    @abstractmethod
    async def initialize(self, ctx: PluginContext) -> None:
        """Called after passport verification and sandbox creation."""

    @abstractmethod
    async def execute(self, payload: dict) -> dict:
        """Invoke the plugin's primary capability."""

    @abstractmethod
    async def shutdown(self) -> None:
        """Cleanup before sandbox teardown."""
