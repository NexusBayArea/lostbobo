from __future__ import annotations

import random
from typing import Any

from backend.core.infisical import get_secret
from backend.core.kernel.command_bus import command_bus
from backend.core.runtime.formalization.invariants import InvariantRegistry
from backend.core.runtime.formalization.state_machine import RuntimeState, RuntimeStateMachine
from backend.core.runtime.state_registry.service import StateRegistryService
from backend.core.runtime.temporal.engine import TemporalEngine
from backend.core.services.observability_service import observability
from backend.core.systems.boundary import ErrorBoundaryService
from backend.core.systems.chaos_service import ChaosService
from backend.core.systems.resource_governance import ResourceGovernor
from backend.core.tracing import trace_context


class ProductionMiddleware:
    """Final production wrapper — outermost middleware in the command chain."""

    async def __call__(self, command: str, **kwargs: Any) -> Any:
        tenant_id = kwargs.get("tenant_id", "default")
        ctx = {"command": command, "tenant": tenant_id}

        with trace_context("production.middleware", ctx) as span:
            # 1. Resource check (hard limits + backpressure)
            if not await ResourceGovernor.governor().check(tenant_id, command):
                return {"status": "rejected", "reason": "resource_limit"}

            # 2. Chaos injection point (only in chaos mode, controlled via Infisical)
            if get_secret("CHAOS_ENABLED", default="false") == "true":
                if random.random() < float(get_secret("CHAOS_INJECTION_PROBABILITY", "0.05")):
                    await ChaosService.chaos().inject(
                        experiment=random.choice(["event_drop", "state_corruption", "temporal_skew"]),
                        intensity=0.3,
                    )

            # 3. State machine transition
            await RuntimeStateMachine.machine().transition(RuntimeState.RUNNING)

            # 4. Full invariant enforcement
            state = await StateRegistryService.registry().get_current()
            event = kwargs.get("event")
            if event and not await InvariantRegistry.invariants().enforce(state, event):
                raise RuntimeError("Invariant violation detected")

            # 5. Error boundary (final safety net)
            async with ErrorBoundaryService.boundary().guard(command):
                # Execute the actual command
                result = await self._execute_command(command, **kwargs)

                # 6. Temporal propagation (only on successful mutation commands)
                if command in ("STATE_MUTATE", "EVENT_PUBLISH"):
                    await TemporalEngine.temporal().propagate(state, event)

            span.set_attribute("status", "success")
            return result

    async def _execute_command(self, command: str, **kwargs: Any) -> Any:
        return await command_bus.execute(command, **kwargs)
