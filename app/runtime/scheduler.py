"""
Scheduler — Topological execution order

Provides deterministic ordering for DAG execution.
"""

from typing import Dict, List


def topological_sort(nodes: Dict[str, "Node"]) -> List[str]:
    visited = set()
    order = []

    def dfs(name: str) -> None:
        if name in visited:
            return
        visited.add(name)

        node = nodes[name]
        for dep in node.deps:
            dfs(dep)

        order.append(name)

    for name in nodes:
        dfs(name)

    return order
