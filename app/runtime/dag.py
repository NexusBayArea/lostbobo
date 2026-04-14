"""
DAG Definition — Deterministic execution graph

Nodes are added with dependencies. DAG validates and provides topological order.
"""

from typing import Callable, Dict, List, Optional


class Node:
    def __init__(self, name: str, fn: Callable, deps: List[str] = None):
        self.name = name
        self.fn = fn
        self.deps = deps or []

    def __repr__(self):
        return f"Node({self.name}, deps={self.deps})"


class DAG:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}

    def add(self, name: str, fn: Callable, deps: List[str] = None) -> "DAG":
        if name in self.nodes:
            raise ValueError(f"Duplicate node: {name}")
        self.nodes[name] = Node(name, fn, deps)
        return self

    def get(self, name: str) -> Optional[Node]:
        return self.nodes.get(name)

    def validate(self) -> None:
        for node in self.nodes.values():
            for dep in node.deps:
                if dep not in self.nodes:
                    raise ValueError(f"Node '{node.name}' depends on missing '{dep}'")

    def __repr__(self):
        return f"DAG(nodes={list(self.nodes.keys())})"
