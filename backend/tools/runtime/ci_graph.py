from dataclasses import dataclass
from typing import Callable, Dict, List, Any


@dataclass
class CINode:
    id: str
    deps: List[str]
    fn: Callable[[], Any]


class CIGraph:
    def __init__(self):
        self.nodes: Dict[str, CINode] = {}

    def add(self, node: CINode):
        self.nodes[node.id] = node

    def topo(self):
        visited = set()
        order = []

        def visit(nid):
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


CI_GRAPH = CIGraph()
