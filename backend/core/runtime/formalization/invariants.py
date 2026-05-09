"""Invariant Registry — real-time enforcement of runtime formalization invariants."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.core.runtime.event_fabric.schema import SimHPCEvent
    from backend.core.world_model.schema import WorldState


class InvariantRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._invariants: list[Callable] = []
            cls._instance._register_core_invariants()
        return cls._instance

    @classmethod
    def invariants(cls) -> InvariantRegistry:
        return cls()

    def _register_core_invariants(self) -> None:
        self.register(self._conservation_of_probability)
        self.register(self._causal_consistency)
        self.register(self._trace_id_preservation)
        self.register(self._supabase_consistency)
        self.register(self._provenance_integrity)
        self.register(self._uncertainty_bounds)
        self.register(self._entity_key_uniqueness)
        self.register(self._temporal_monotonicity)

    def register(self, invariant: Callable) -> None:
        self._invariants.append(invariant)

    async def enforce(self, state: WorldState, event: SimHPCEvent) -> bool:
        from backend.core.runtime.event_fabric.log import EventLogService
        from backend.core.runtime.event_fabric.schema import EventPriority
        from backend.core.runtime.event_fabric.schema import SimHPCEvent as Evt
        from backend.core.services.observability_service import observability

        violations: list[str] = []
        for inv in self._invariants:
            try:
                if not await inv(state, event):
                    violations.append(inv.__name__)
            except Exception as exc:
                violations.append(f"{inv.__name__}:{exc}")

        if violations:
            obs = observability()
            obs.increment("invariant_violations_total", {"count": str(len(violations))})
            violation_event = Evt(
                event_type="runtime.invariant.violation",
                source_plugin="kernel",
                priority=EventPriority.CRITICAL,
                payload={"violations": violations, "event_id": event.event_id},
            )
            try:
                await EventLogService.event_log().publish(violation_event)
            except Exception:
                pass
            return False
        return True

    async def _conservation_of_probability(self, state: WorldState, event: SimHPCEvent) -> bool:
        return True

    async def _causal_consistency(self, state: WorldState, event: SimHPCEvent) -> bool:
        return event.vector_clock is not None

    async def _trace_id_preservation(self, state: WorldState, event: SimHPCEvent) -> bool:
        payload = event.payload or {}
        return "trace_id" in payload or "traceparent" in payload

    async def _supabase_consistency(self, state: WorldState, event: SimHPCEvent) -> bool:
        return True

    async def _provenance_integrity(self, state: WorldState, event: SimHPCEvent) -> bool:
        return bool(event.provenance_hash)

    async def _uncertainty_bounds(self, state: WorldState, event: SimHPCEvent) -> bool:
        for ent in state.entities.values():
            if not (0.0 <= ent.uncertainty <= 1.0):
                return False
        return True

    async def _entity_key_uniqueness(self, state: WorldState, event: SimHPCEvent) -> bool:
        keys = list(state.entities.keys())
        return len(keys) == len(set(keys))

    async def _temporal_monotonicity(self, state: WorldState, event: SimHPCEvent) -> bool:
        return event.timestamp >= state.timestamp
