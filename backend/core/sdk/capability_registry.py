from __future__ import annotations

from collections.abc import Callable
from typing import Any

CapabilityHandler = Callable[[dict], Any]


class CapabilityRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, CapabilityHandler] = {}

    def register(
        self,
        capability: str,
        handler: CapabilityHandler,
    ) -> None:
        if capability in self._handlers:
            raise ValueError(f"Capability already registered: {capability}")

        self._handlers[capability] = handler

    async def invoke(
        self,
        capability: str,
        payload: dict,
    ) -> Any:
        if capability not in self._handlers:
            raise KeyError(f"Unknown capability: {capability}")

        handler = self._handlers[capability]

        return await handler(payload)

    def validate(
        self,
        capabilities: list[str],
        allowed_permissions: list[str],
    ) -> list[str]:
        invalid = [c for c in capabilities if c not in allowed_permissions]
        if invalid:
            raise ValueError(f"Capabilities {invalid} not declared in passport permissions")
        return capabilities

    def list_capabilities(self) -> list[str]:
        return list(self._handlers.keys())
