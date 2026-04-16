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
        self.nodes[node.id] = node

    def get(self, node_id: str) -> Node:
        return self.nodes[node_id]


GRAPH = ExecutionGraph()
