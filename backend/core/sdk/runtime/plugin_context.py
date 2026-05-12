from __future__ import annotations

import logging


class PluginContext:
    def __init__(self, plugin_id: str, permissions: list[str], kernel):
        self.plugin_id = plugin_id
        self._permissions = set(permissions)
        self._kernel = kernel
        self._logger = logging.getLogger(f"plugin.{plugin_id}")

    def _check(self, permission: str):
        if permission not in self._permissions:
            raise PermissionError(f"plugin {self.plugin_id} missing permission: {permission}")

    @property
    def capabilities(self):
        self._check("kernel.events")
        return self._kernel.capabilities

    async def memory_store(self, key: str, value: str):
        self._check("memory.write")
        return await self._kernel.memory.insert({"key": key, "value": value})

    async def memory_read(self, key: str) -> str | None:
        self._check("memory.read")
        return await self._kernel.memory.lookup({"key": key})

    async def emit_event(self, event_type: str, payload: dict):
        self._check("kernel.events")
        await self._kernel.stream_manager.event_bus.publish(event_type, payload)

    async def emit_telemetry(self, event_type: str, metadata: dict):
        await self._kernel.trust_telemetry.report(
            event_type=event_type,
            plugin_id=self.plugin_id,
            details=metadata,
        )

    @property
    def logger(self) -> logging.Logger:
        return self._logger
