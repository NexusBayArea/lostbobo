from __future__ import annotations

from typing import Any


class GraphStore:
    def __init__(self):
        self._edges: list[dict[str, Any]] = []

    def add_edge(self, source: str, target: str, edge_type: str = "related", metadata: dict | None = None):
        self._edges.append(
            {
                "source": source,
                "target": target,
                "edge_type": edge_type,
                "metadata": metadata or {},
            }
        )

    @property
    def edges(self) -> list[dict[str, Any]]:
        return self._edges

    def get_neighbors(self, node_id: str) -> list[str]:
        neighbors = set()
        for e in self._edges:
            if e["source"] == node_id:
                neighbors.add(e["target"])
            if e["target"] == node_id:
                neighbors.add(e["source"])
        return list(neighbors)
