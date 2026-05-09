"""Vector clock for multi-source causal ordering."""

from __future__ import annotations


class VectorClock(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setdefault("kernel", 0)

    def increment(self, source: str = "kernel") -> VectorClock:
        self[source] = self.get(source, 0) + 1
        return self

    def merge(self, other: VectorClock) -> VectorClock:
        for k, v in other.items():
            self[k] = max(self.get(k, 0), v)
        return self

    def __le__(self, other: VectorClock) -> bool:
        return all(self.get(k, 0) <= other.get(k, 0) for k in set(self) | set(other))

    def __repr__(self) -> str:
        return f"VectorClock({dict.__repr__(self)})"
