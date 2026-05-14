from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class PluginState(str, Enum):
    REGISTERED = "registered"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    DEGRADED = "degraded"
    TERMINATING = "terminating"
    TERMINATED = "terminated"
    FAILED = "failed"


VALID_TRANSITIONS: dict[PluginState, set[PluginState]] = {
    PluginState.REGISTERED: {PluginState.INITIALIZING, PluginState.TERMINATED},
    PluginState.INITIALIZING: {PluginState.RUNNING, PluginState.FAILED},
    PluginState.RUNNING: {PluginState.PAUSED, PluginState.DEGRADED, PluginState.TERMINATING, PluginState.FAILED},
    PluginState.PAUSED: {PluginState.RUNNING, PluginState.TERMINATING, PluginState.FAILED},
    PluginState.DEGRADED: {PluginState.RUNNING, PluginState.TERMINATING, PluginState.FAILED},
    PluginState.TERMINATING: {PluginState.TERMINATED, PluginState.FAILED},
    PluginState.TERMINATED: set(),
    PluginState.FAILED: {PluginState.TERMINATING},
}


@dataclass
class LifecycleEvent:
    state: PluginState
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class InvalidLifecycleTransitionError(Exception):
    pass


class LifecycleManager:
    def __init__(self, plugin_name: str):
        self.plugin_name = plugin_name
        self.current_state = PluginState.REGISTERED
        self.history: list[LifecycleEvent] = [LifecycleEvent(PluginState.REGISTERED)]

    def can_transition(self, target: PluginState) -> bool:
        return target in VALID_TRANSITIONS.get(self.current_state, set())

    def transition(
        self,
        target: PluginState,
        reason: str | None = None,
        metadata: dict | None = None,
    ) -> LifecycleEvent:
        if not self.can_transition(target):
            raise InvalidLifecycleTransitionError(
                f"Cannot transition {self.plugin_name} from {self.current_state} to {target}"
            )
        self.current_state = target
        event = LifecycleEvent(state=target, reason=reason, metadata=metadata or {})
        self.history.append(event)
        return event
