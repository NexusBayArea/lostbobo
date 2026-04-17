from dataclasses import dataclass
from typing import Callable, Dict, List, Any


@dataclass
class Node:
    id: str
    fn: Callable[..., Any]
    deps: List[str]


class ExecutionGraph:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}

    def register(self, node: Node):
        if node.id in self.nodes:
            raise ValueError(f"Duplicate node: {node.id}")
        self.nodes[node.id] = node

    def get(self, node_id: str) -> Node:
        return self.nodes[node_id]

    def topologically_sorted(self) -> List[str]:
        visited = set()
        visiting = set()
        order = []

        def visit(nid: str):
            if nid in visiting:
                raise RuntimeError(f"Cyclic dependency detected at node: {nid}")
            if nid in visited:
                return

            visiting.add(nid)
            node = self.nodes[nid]
            for d in node.deps:
                visit(d)

            visiting.remove(nid)
            visited.add(nid)
            order.append(nid)

        for n in self.nodes:
            visit(n)

        return order


GRAPH = ExecutionGraph()
