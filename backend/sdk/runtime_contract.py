# backend/sdk/runtime_contract.py
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

log = logging.getLogger(__name__)


class PluginRuntimeContract(ABC):
    """Canonical contract every plugin receives via self.runtime."""

    @abstractmethod
    async def observe(self, entity_keys: list[str] | None = None) -> dict:
        """Observe current world state (filtered or full snapshot)."""

    @abstractmethod
    async def emit(
        self,
        event_type: str,
        payload: dict[str, Any],
        confidence: float = 0.8,
        entity_key: str | None = None,
    ) -> str:
        """Emit event through Event Fabric -> mutates WorldState."""

    @abstractmethod
    async def forecast(self, entity_key: str, horizon: datetime | None = None) -> dict[str, Any]:
        """Request a forecast from the temporal probabilistic engine."""

    @abstractmethod
    @property
    def world(self) -> WorldService:
        """Canonical WorldService — use self.runtime.world everywhere."""
        if not hasattr(self, "_world_service"):
            from backend.sdk.world_service import WorldServiceImpl

            self._world_service = WorldServiceImpl(self.plugin_id, self._kernel)
        return self._world_service


class DefaultRuntimeContract(PluginRuntimeContract):
    """Default implementation attached to every plugin."""

    def __init__(self, plugin_id: str, kernel_gateway):
        self.plugin_id = plugin_id
        self._kernel = kernel_gateway

    async def observe(self, entity_keys: list[str] | None = None) -> dict:
        """Observe current world state."""
        try:
            from backend.core.runtime.state_registry.service import (
                StateRegistryService,
            )

            registry = StateRegistryService()
            return await registry.get_snapshot(entity_keys=entity_keys)
        except Exception as e:
            log.error("Runtime contract observe failed: %s", e)
            return {}

    async def emit(
        self,
        event_type: str,
        payload: dict[str, Any],
        confidence: float = 0.8,
        entity_key: str | None = None,
    ) -> str:
        """Emit event -> Event Fabric -> WorldState mutation."""
        try:
            from backend.core.runtime.event_fabric.log import EventLogService

            event = {
                "event_type": event_type,
                "source_plugin": self.plugin_id,
                "confidence": confidence,
                "payload": payload,
                "entity_key": entity_key,
            }
            return await EventLogService().publish(event)
        except Exception as e:
            log.error("Runtime contract emit failed: %s", e)
            return ""

    async def forecast(self, entity_key: str, horizon: datetime | None = None) -> dict[str, Any]:
        """Request forecast from Temporal Engine."""
        try:
            from backend.core.runtime.temporal.engine import TemporalEngine

            engine = TemporalEngine()
            result = await engine.forecast_entity(entity_key, horizon=horizon)
            return result.to_dict() if hasattr(result, "to_dict") else result
        except Exception as e:
            log.error("Runtime contract forecast failed: %s", e)
            return {}

    async def mutate(
        self,
        entity_key: str,
        attribute: str,
        value: Any,
        uncertainty: dict | None = None,
        confidence: float = 0.85,
    ) -> bool:
        """Mutate world state canonically."""
        try:
            from backend.core.runtime.state_registry.service import (
                StateRegistryService,
            )

            registry = StateRegistryService()
            return await registry.mutate_entity(
                entity_key=entity_key,
                attribute=attribute,
                value=value,
                uncertainty=uncertainty,
                confidence=confidence,
                source=f"plugin:{self.plugin_id}",
            )
        except Exception as e:
            log.error("Runtime contract mutate failed: %s", e)
            return False
