from __future__ import annotations

from enum import Enum

from backend.core.services.observability_service import observability
from backend.core.tracing import trace_context


class RuntimeState(str, Enum):
    INITIALIZING = "initializing"
    RUNNING = "running"
    DEGRADED = "degraded"
    PAUSED = "paused"
    SHUTTING_DOWN = "shutting_down"
    ERROR = "error"


class RuntimeStateMachine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._current_state = RuntimeState.INITIALIZING
            cls._instance._transitions: dict[RuntimeState, set[RuntimeState]] = {
                RuntimeState.INITIALIZING: {RuntimeState.RUNNING, RuntimeState.ERROR},
                RuntimeState.RUNNING: {
                    RuntimeState.DEGRADED,
                    RuntimeState.PAUSED,
                    RuntimeState.SHUTTING_DOWN,
                    RuntimeState.ERROR,
                },
                RuntimeState.DEGRADED: {
                    RuntimeState.RUNNING,
                    RuntimeState.PAUSED,
                    RuntimeState.ERROR,
                },
                RuntimeState.PAUSED: {
                    RuntimeState.RUNNING,
                    RuntimeState.SHUTTING_DOWN,
                    RuntimeState.ERROR,
                },
                RuntimeState.SHUTTING_DOWN: {RuntimeState.ERROR},
                RuntimeState.ERROR: {RuntimeState.INITIALIZING},
            }
        return cls._instance

    @classmethod
    def machine(cls) -> RuntimeStateMachine:
        return cls()

    async def transition(self, to_state: RuntimeState, reason: str = "") -> bool:
        with trace_context(
            "runtime.state.transition",
            {"from": self._current_state, "to": to_state},
        ) as span:
            if to_state not in self._transitions.get(self._current_state, set()):
                observability().increment("state_transition_violations")
                return False

            self._current_state = to_state
            observability().gauge("runtime_state", {"state": to_state})
            span.set_attribute("new_state", to_state)
            return True

    def get_current(self) -> RuntimeState:
        return self._current_state
