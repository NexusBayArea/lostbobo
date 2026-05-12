from backend.core.world.fabric.vector_clock import VectorClock


class CausalityResolver:
    @staticmethod
    def resolve(events: list["WorldEvent"]) -> list["WorldEvent"]:
        clocks = {e.event_id: VectorClock.from_dict(e.vector_clock) for e in events}
        # Rough order by timestamp first
        sorted_events = sorted(events, key=lambda e: e.timestamp)

        result = []
        remaining = {e.event_id for e in events}

        while remaining:
            # find ready events (no remaining predecessor)
            ready = []
            for eid in remaining:
                is_ready = True
                for other_id in remaining:
                    if eid == other_id:
                        continue
                    if clocks[other_id].happens_before(clocks[eid]):
                        is_ready = False
                        break
                if is_ready:
                    ready.append(eid)

            if not ready:
                # concurrency detected; pick smallest event_id for determinism
                ready = [sorted(remaining)[0]]

            ready_id = ready[0]
            result.append(next(e for e in events if e.event_id == ready_id))
            remaining.remove(ready_id)

        return result
