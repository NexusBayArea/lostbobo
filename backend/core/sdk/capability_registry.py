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

    def list_capabilities(self) -> list[str]:
        return list(self._handlers.keys())
