"""State Registry Service — canonical world state with causal + temporal guarantees."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable

from backend.app.core.supabase import get_supabase_client
from backend.core.runtime.event_fabric.log import EventLogService
from backend.core.runtime.event_fabric.schema import SimHPCEvent
from backend.core.runtime.temporal.engine import temporal_engine
from backend.core.services.observability_service import observability
from backend.core.services.tracing import tracer

log = logging.getLogger(__name__)


class StateRegistryService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._current_state = None
            cls._instance._supabase = get_supabase_client()
            cls._instance._observers: list[Callable] = []
            cls._instance._pending_mutations: list[SimHPCEvent] = []
            cls._instance._initialized = False
        return cls._instance

    @classmethod
    def registry(cls) -> StateRegistryService:
        return cls()

    def _ensure_init(self) -> None:
        if not self._initialized:
            from backend.core.world_model.schema import WorldState

            self._current_state = WorldState()
            self._initialized = True

    async def mutate(self, event: SimHPCEvent) -> WorldState:  # noqa: F821
        self._ensure_init()
        with tracer.start_as_current_span(
            "state.mutate",
            attributes={"event_type": event.event_type},
        ):
            obs = observability()
            obs.increment("state_mutations_total")

            if not EventLogService.event_log()._is_causally_ready(event):
                self._pending_mutations.append(event)
                return self._current_state

            new_state = self._current_state.apply_event(event)
            new_state = await temporal_engine().propagate(new_state, event)
            self._current_state = new_state

            if self._supabase:
                try:
                    self._supabase.table("world_states").insert(
                        {
                            **new_state.model_dump(),
                            "snapshot_at": time.time(),
                        }
                    ).execute()
                except Exception as exc:
                    log.error("Failed to persist world state: %s", exc)

            await self._notify_observers(new_state)
            await self._drain_pending()

        obs.gauge("world_state_size", len(new_state.entities))
        return new_state

    async def _notify_observers(self, state: WorldState) -> None:  # noqa: F821
        for obs_handler in self._observers:
            try:
                if asyncio.iscoroutinefunction(obs_handler):
                    asyncio.create_task(obs_handler(state))
                else:
                    obs_handler(state)
            except Exception as exc:
                log.warning("Observer error: %s", exc)
                observability().increment("observer_errors_total")

    async def _drain_pending(self) -> None:
        still_pending = []
        for event in self._pending_mutations:
            if EventLogService.event_log()._is_causally_ready(event):
                await self.mutate(event)
            else:
                still_pending.append(event)
        self._pending_mutations = still_pending

    async def observe(self, handler: Callable) -> None:
        self._observers.append(handler)

    async def get_current(self) -> WorldState:  # noqa: F821
        self._ensure_init()
        return self._current_state

    async def reconstruct(self, at_timestamp: float) -> WorldState:  # noqa: F821
        from backend.core.world_model.schema import WorldState

        events = await EventLogService.event_log().replay(from_ts=0, to_ts=at_timestamp)
        state = WorldState()
        for ev in events:
            state = state.apply_event(ev)
            state = await temporal_engine().propagate(state, ev)
        return state
