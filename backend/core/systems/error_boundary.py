from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from backend.core.runtime.event_fabric.log import EventLogService
from backend.core.runtime.event_fabric.schema import SimHPCEvent
from backend.core.runtime.formalization.state_machine import RuntimeState, RuntimeStateMachine
from backend.core.runtime.state_registry.service import StateRegistryService
from backend.core.services.observability_service import observability
from backend.core.tracing import trace_context


class ErrorBoundaryService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def boundary(cls) -> ErrorBoundaryService:
        return cls()

    @asynccontextmanager
    async def guard(self, command_name: str) -> AsyncIterator[None]:
        """Wraps every Kernel command with snapshot + rollback + circuit breaker."""
        with trace_context("error.boundary", {"command": command_name}):
            obs = observability()
            snapshot = await StateRegistryService.registry().get_current()

            try:
                yield
            except Exception as exc:
                obs.increment("error_boundary_triggered", tags={"command": command_name})
                await EventLogService.event_log().publish(
                    SimHPCEvent(
                        event_type="runtime.error.boundary_triggered",
                        source_plugin="kernel",
                        priority="critical",
                        payload={"command": command_name, "error": str(exc)},
                    )
                )
                # Rollback to last consistent state
                await StateRegistryService.registry().reconstruct(snapshot.timestamp)
                await RuntimeStateMachine.machine().transition(RuntimeState.DEGRADED, reason=str(exc))
                raise
