from collections import defaultdict


class VectorClock:
    def __init__(self):
        self.clock = defaultdict(int)

    def increment(self, node_id: str):
        self.clock[node_id] += 1

    def merge(self, other: "VectorClock"):
        for node, counter in other.clock.items():
            self.clock[node] = max(self.clock[node], counter)

    def happens_before(self, other: "VectorClock") -> bool:
        """True if self < other in the partial order."""
        strictly_less = False
        all_nodes = set(self.clock.keys()) | set(other.clock.keys())
        for node in all_nodes:
            a = self.clock.get(node, 0)
            b = other.clock.get(node, 0)
            if a > b:
                return False
            if a < b:
                strictly_less = True
        return strictly_less

    def to_dict(self) -> dict:
        return dict(self.clock)

    @classmethod
    def from_dict(cls, d: dict) -> "VectorClock":
        vc = cls()
        vc.clock = defaultdict(int, d)
        return vc
