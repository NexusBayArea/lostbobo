from __future__ import annotations

from collections.abc import Callable
from typing import Any

NodeExecutor = Callable[[dict], Any]


class DAGNodeRegistry:
    def __init__(self) -> None:
        self._nodes: dict[str, NodeExecutor] = {}

    def register_node(
        self,
        node_type: str,
        executor: NodeExecutor,
    ) -> None:
        if node_type in self._nodes:
            raise ValueError(f"DAG node already registered: {node_type}")

        self._nodes[node_type] = executor

    async def execute_node(
        self,
        node_type: str,
        payload: dict,
    ) -> Any:
        if node_type not in self._nodes:
            raise KeyError(f"Unknown DAG node: {node_type}")

        executor = self._nodes[node_type]

        return await executor(payload)

    def list_nodes(self) -> list[str]:
        return list(self._nodes.keys())
