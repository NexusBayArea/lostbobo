from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any


class DAGNodeAlreadyRegisteredError(Exception):
    pass


class DAGNodeNotFoundError(Exception):
    pass


NodeExecutor = Callable[[dict], Awaitable[Any]]


@dataclass
class DAGNodeEntry:
    node_type: str
    executor: NodeExecutor
    plugin_name: str
    version: str = "1.0.0"
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    deterministic: bool = True
    idempotent: bool = True
    max_retries: int = 0
    timeout_seconds: int = 300


class DAGNodeRegistry:
    def __init__(self):
        self._nodes: dict[str, DAGNodeEntry] = {}

    def register_node(
        self,
        node_type: str,
        executor: NodeExecutor,
        plugin_name: str,
        version: str = "1.0.0",
        input_schema: dict | None = None,
        output_schema: dict | None = None,
        deterministic: bool = True,
        idempotent: bool = True,
        max_retries: int = 0,
        timeout_seconds: int = 300,
    ) -> None:
        if node_type in self._nodes:
            raise DAGNodeAlreadyRegisteredError(
                f"DAG node '{node_type}' already registered by '{self._nodes[node_type].plugin_name}'"
            )
        self._nodes[node_type] = DAGNodeEntry(
            node_type=node_type,
            executor=executor,
            plugin_name=plugin_name,
            version=version,
            input_schema=input_schema or {},
            output_schema=output_schema or {},
            deterministic=deterministic,
            idempotent=idempotent,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
        )

    def unregister_node(self, node_type: str) -> None:
        self._nodes.pop(node_type, None)

    def get_node(self, node_type: str) -> DAGNodeEntry:
        entry = self._nodes.get(node_type)
        if not entry:
            raise DAGNodeNotFoundError(f"DAG node '{node_type}' not registered")
        return entry

    def get_executor(self, node_type: str) -> NodeExecutor | None:
        entry = self._nodes.get(node_type)
        return entry.executor if entry else None

    async def execute_node(self, node_type: str, inputs: dict[str, Any]) -> Any:
        entry = self.get_node(node_type)
        return await entry.executor(inputs)

    @property
    def registered_nodes(self) -> list[str]:
        return list(self._nodes.keys())


class DAGRegistry(DAGNodeRegistry):
    pass
