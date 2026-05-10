from __future__ import annotations

from .storage import TemporalState


class TimelineReplay:
    def __init__(self):
        self.states: list[TemporalState] = []

    def append(self, state: TemporalState):
        self.states.append(state)

    def replay(self, start: int = 0, end: int | None = None) -> list[TemporalState]:
        return self.states[start:end]
