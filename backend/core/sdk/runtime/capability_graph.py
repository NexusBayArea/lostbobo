from __future__ import annotations

from collections import defaultdict


class CapabilityGraph:
    def __init__(self):
        self._edges: dict[str, set[str]] = defaultdict(set)
        self._reverse_edges: dict[str, set[str]] = defaultdict(set)

    def add_dependency(self, source: str, target: str) -> None:
        self._edges[source].add(target)
        self._reverse_edges[target].add(source)

    def remove_dependency(self, source: str, target: str) -> None:
        self._edges[source].discard(target)
        self._reverse_edges[target].discard(source)

    def remove_plugin(self, plugin_name: str) -> None:
        for deps in self._edges.values():
            deps.discard(plugin_name)
        for deps in self._reverse_edges.values():
            deps.discard(plugin_name)
        self._edges.pop(plugin_name, None)
        self._reverse_edges.pop(plugin_name, None)

    def dependencies_of(self, plugin: str) -> set[str]:
        return self._edges.get(plugin, set()).copy()

    def dependents_of(self, plugin: str) -> set[str]:
        return self._reverse_edges.get(plugin, set()).copy()

    def has_cycle(self) -> bool:
        visited: set[str] = set()
        recursion_stack: set[str] = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            recursion_stack.add(node)
            for neighbor in self._edges.get(node, set()):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in recursion_stack:
                    return True
            recursion_stack.discard(node)
            return False

        for node in list(self._edges.keys()):
            if node not in visited:
                if dfs(node):
                    return True
        return False

    def topological_sort(self) -> list[str]:
        if self.has_cycle():
            raise ValueError("Cannot topological sort: graph contains a cycle")

        in_degree: dict[str, int] = defaultdict(int)
        for node, deps in self._edges.items():
            if node not in in_degree:
                in_degree[node] = 0
            for dep in deps:
                in_degree[dep] += 1

        queue = [node for node, deg in in_degree.items() if deg == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)
            for dependent in self._reverse_edges.get(node, set()):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        return result

    @property
    def nodes(self) -> list[str]:
        return list(set(list(self._edges.keys()) + list(self._reverse_edges.keys())))

    @property
    def edge_count(self) -> int:
        return sum(len(deps) for deps in self._edges.values())
