from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from backend.core.sdk.abi.lifecycle import LifecycleManager, PluginState
from backend.core.sdk.abi.permissions import PermissionSet


@dataclass
class PluginContext:
    plugin_name: str
    manifest_version: str

    lifecycle: LifecycleManager = field(init=False)
    permissions: PermissionSet | None = None

    assigned_gpu_id: int | None = None
    assigned_gpu_fraction: float | None = None
    assigned_memory_mb: int = 0

    isolation_tier: str = "process"
    sandbox_handle: Any | None = None

    plugin_instance: Any | None = None

    start_time: float | None = None
    total_invocations: int = 0
    total_errors: int = 0
    last_error: str | None = None

    _kernel: Any = None
    _logger: logging.Logger = field(init=False)

    def __post_init__(self):
        self.lifecycle = LifecycleManager(self.plugin_name)
        self._logger = logging.getLogger(f"plugin.{self.plugin_name}")

    @property
    def is_healthy(self) -> bool:
        return self.lifecycle.current_state in {
            PluginState.RUNNING,
            PluginState.DEGRADED,
        }

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    def check_permission(self, syscall: str) -> bool:
        if self.permissions is None:
            return False
        from backend.core.sdk.abi.permissions import Syscall

        try:
            return self.permissions.check_syscall(Syscall(syscall))
        except ValueError:
            return False

    async def emit_event(self, event_type: str, payload: dict[str, Any]) -> None:
        if self._kernel is None:
            raise RuntimeError("PluginContext not bound to kernel")
        if not self.check_permission("event.emit"):
            raise PermissionError(f"Plugin {self.plugin_name} missing permission: event.emit")
        await self._kernel.events.emit(event_type, payload)

    def record_invocation(self, success: bool, error: str | None = None):
        self.total_invocations += 1
        if not success:
            self.total_errors += 1
            self.last_error = error
