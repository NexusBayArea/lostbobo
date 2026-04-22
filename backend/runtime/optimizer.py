from typing import Any

from runtime.contract import CONTRACT


class DAGOptimizer:
    def __init__(self, dag: dict[str, Any]):
        self.dag = dag

    def optimize(self, trace=None) -> dict[str, Any]:
        dag = self.dag.copy()

        dag = self._prune_invalid(dag)
        dag = self._remove_dead_nodes(dag)
        dag = self._dedupe(dag)

        if trace:
            dag = self._prune_slow_nodes(dag, trace)

        return dag

    def _prune_invalid(self, dag):
        valid = {}

        for name, node in dag.items():
            # Adjusting to use CONTRACT properties
            module = node.get("path", "")

            # Assuming allowed_roots from contract can act as module validation
            if CONTRACT.is_allowed_root(module):
                valid[name] = node

        return valid

    def _remove_dead_nodes(self, dag):
        # remove nodes with no dependencies and no consumers
        used = set()

        for n in dag.values():
            for d in n.get("depends_on", []):
                used.add(d)

        return {k: v for k, v in dag.items() if k in used or v.get("depends_on")}

    def _dedupe(self, dag):
        seen = {}
        result = {}

        for k, v in dag.items():
            key = str(v)

            if key not in seen:
                seen[key] = k
                result[k] = v

        return result

    def _prune_slow_nodes(self, dag, trace):
        # Assuming trace structure matches Trace class
        slow_nodes = [
            name
            for name, data in trace.get("nodes", {}).items()
            if data.get("duration", 0) > 1.0  # seconds
        ]

        return {k: v for k, v in dag.items() if k not in slow_nodes}
