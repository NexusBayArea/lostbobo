from backend.core.world.fabric.event_log import WorldEvent
from backend.core.world.fabric.vector_clock import VectorClock


class CausalityResolver:
    @staticmethod
    def resolve(events: list[WorldEvent]) -> list[WorldEvent]:
        clocks = {e.event_id: VectorClock.from_dict(e.vector_clock) for e in events}

        result = []
        remaining = {e.event_id for e in events}

        while remaining:
            ready = []
            for eid in remaining:
                if not any(clocks[other].happens_before(clocks[eid]) for other in remaining if other != eid):
                    ready.append(eid)

            if not ready:
                ready = [min(remaining)]

            eid = ready[0] if len(ready) == 1 else min(ready)
            result.append(next(e for e in events if e.event_id == eid))
            remaining.remove(eid)

        return result
