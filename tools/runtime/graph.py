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
        order = []

        def visit(nid: str):
            if nid in visited:
                return
            node = self.nodes[nid]
            for d in node.deps:
                visit(d)
            visited.add(nid)
            order.append(nid)

        for n in self.nodes:
            visit(n)

        return order


GRAPH = ExecutionGraph()
