from __future__ import annotations

import logging


class _MemoryACL:
    def __init__(self, plugin_id: str, permissions: set[str], kernel):
        self._plugin_id = plugin_id
        self._permissions = permissions
        self._kernel = kernel

    async def store(self, key: str, value: str):
        if "memory.write" not in self._permissions:
            raise PermissionError(f"plugin {self._plugin_id} missing permission: memory.write")
        return await self._kernel.memory.insert({"key": key, "value": value})

    async def read(self, key: str) -> str | None:
        if "memory.read" not in self._permissions:
            raise PermissionError(f"plugin {self._plugin_id} missing permission: memory.read")
        return await self._kernel.memory.lookup({"key": key})


class _TelemetryACL:
    def __init__(self, plugin_id: str, kernel):
        self._plugin_id = plugin_id
        self._kernel = kernel

    async def emit(self, event_type: str, metadata: dict):
        await self._kernel.trust_telemetry.report(
            event_type=event_type,
            plugin_id=self._plugin_id,
            details=metadata,
        )


class PluginContext:
    def __init__(self, plugin_id: str, permissions: list[str], kernel):
        self.plugin_id = plugin_id
        self._permissions = set(permissions)
        self._kernel = kernel
        self._logger = logging.getLogger(f"plugin.{plugin_id}")
        self._memory = _MemoryACL(plugin_id, self._permissions, kernel)
        self._telemetry = _TelemetryACL(plugin_id, kernel)

    def _check(self, permission: str):
        if permission not in self._permissions:
            raise PermissionError(f"plugin {self.plugin_id} missing permission: {permission}")

    @property
    def memory(self) -> _MemoryACL:
        return self._memory

    @property
    def telemetry(self) -> _TelemetryACL:
        return self._telemetry

    @property
    def capabilities(self):
        self._check("kernel.events")
        return self._kernel.capabilities

    async def emit_event(self, event_type: str, payload: dict):
        self._check("kernel.events")
        await self._kernel.stream_manager.event_bus.publish(event_type, payload)

    async def emit_telemetry(self, event_type: str, metadata: dict):
        await self._telemetry.emit(event_type, metadata)

    async def talk_to(
        self,
        target_plugin: str,
        requested_capabilities: list[str],
    ) -> str | None:
        from backend.core.sdk.handshake_client import request_session

        return await request_session(
            kernel_bus=self._kernel.protocol_bus,
            source_plugin=self.plugin_id,
            target_plugin=target_plugin,
            requested_capabilities=requested_capabilities,
        )

    @property
    def logger(self) -> logging.Logger:
        return self._logger
