"""
Scheduler — Topological execution order + queue-driven execution

Provides:
- topological_sort: deterministic ordering
- Scheduler: queue-driven execution with backpressure
"""

from typing import Any, Dict, List

from app.runtime.queue import TaskQueue


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


class Scheduler:
    def __init__(self, dag):
        self.dag = dag
        self.queue = TaskQueue()
        self.results = {}

    def seed(self) -> None:
        for name, node in self.dag.nodes.items():
            if not node.deps:
                self.queue.push(name)

    def ready(self, node_name: str) -> bool:
        node = self.dag.nodes[node_name]
        return all(dep in self.results for dep in node.deps)

    def run(self, dispatch: Any, context: Dict[str, Any] = None) -> Dict[str, Any]:
        context = context or {}
        self.seed()

        cycles = 0
        max_cycles = len(self.dag.nodes) * 2

        while not self.queue.empty():
            if cycles > max_cycles:
                raise RuntimeError("Scheduler deadlock detected")
            cycles += 1

            name = self.queue.pop()
            node = self.dag.nodes[name]

            if not self.ready(name):
                self.queue.push(name)
                continue

            inputs = {dep: self.results[dep] for dep in node.deps}

            result = dispatch(node, inputs, context)
            self.results[name] = result

            for n, other in self.dag.nodes.items():
                if name in other.deps:
                    if self.ready(n):
                        self.queue.push(n)

        return self.results
