from typing import Dict, List, Any


class DiffResult:
    def __init__(self):
        self.changed = {}
        self.added = {}
        self.removed = {}

    def to_dict(self):
        return {
            "changed": self.changed,
            "added": self.added,
            "removed": self.removed,
        }


class TraceDiffer:
    def __init__(self, trace_a: List[dict], trace_b: List[dict]):
        self.a = {t["node"]: t for t in trace_a}
        self.b = {t["node"]: t for t in trace_b}

    def diff(self) -> Dict[str, Any]:
        result = DiffResult()

        keys_a = set(self.a.keys())
        keys_b = set(self.b.keys())

        for k in keys_a & keys_b:
            if self.a[k]["outputs"] != self.b[k]["outputs"]:
                result.changed[k] = {
                    "before": self.a[k]["outputs"],
                    "after": self.b[k]["outputs"],
                }

        for k in keys_b - keys_a:
            result.added[k] = self.b[k]

        for k in keys_a - keys_b:
            result.removed[k] = self.a[k]

        return result.to_dict()
