from collections import defaultdict


class VectorClock:
    def __init__(self):
        self.clock: dict[str, int] = defaultdict(int)

    def happens_before(self, other: "VectorClock") -> bool:
        # returns True if self happens before other
        any_less = False
        for k in set(self.clock.keys()) | set(other.clock.keys()):
            if self.clock[k] > other.clock[k]:
                return False
            if self.clock[k] < other.clock[k]:
                any_less = True
        return any_less

    @classmethod
    def from_dict(cls, d: dict[str, int]):
        vc = cls()
        vc.clock = defaultdict(int, d)
        return vc
