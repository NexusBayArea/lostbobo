from typing import Any

from backend.runtime.contract import CONTRACT


class DAGOptimizer:
    def optimize(self, dag: dict[str, Any], trace: dict | None = None) -> dict[str, Any]:
        """Optimize DAG: prune invalid, dead, and slow nodes."""
        dag = self._prune_invalid(dag)
        dag = self._remove_dead_nodes(dag)
        dag = self._deduplicate(dag)

        if trace:
            dag = self._prune_slow_nodes(dag, trace)

        return dag

    def _prune_invalid(self, dag: dict) -> dict:
        return {k: v for k, v in dag.items() if CONTRACT.is_allowed_root(v.get("path", ""))}

    def _remove_dead_nodes(self, dag: dict) -> dict:
        used = set()
        for node in dag.values():
            for dep in node.get("depends_on", []):
                used.add(dep)
        return {k: v for k, v in dag.items() if k in used or v.get("depends_on")}

    def _deduplicate(self, dag: dict) -> dict:
        seen = {}
        result = {}
        for k, v in dag.items():
            key = str(sorted(v.items()))
            if key not in seen:
                seen[key] = k
                result[k] = v
        return result

    def _prune_slow_nodes(self, dag: dict, trace: dict) -> dict:
        slow = {n for n, data in trace.get("nodes", {}).items() if data.get("duration_ms", 0) > 5000}
        return {k: v for k, v in dag.items() if k not in slow}
