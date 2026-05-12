from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

from backend.core.skill.models import CapabilityDefinition


class CapabilityRegistry:
    def __init__(self, kernel):
        self._capabilities: dict[str, CapabilityDefinition] = {}
        self._plugin_capabilities: dict[str, list[str]] = defaultdict(list)
        self.kernel = kernel
        self._dependents_graph: dict[str, set[str]] = defaultdict(set)

    def register(self, definition: CapabilityDefinition):
        name = definition.name
        if name in self._capabilities:
            raise ValueError(f"Capability {name} already registered")
        self._capabilities[name] = definition
        self._plugin_capabilities[definition.plugin_name].append(name)
        for dep in definition.dependencies:
            self._dependents_graph[dep].add(name)

    def unregister(self, name: str):
        if name not in self._capabilities:
            return
        cap_def = self._capabilities[name]
        del self._capabilities[name]

        if name in self._plugin_capabilities[cap_def.plugin_name]:
            self._plugin_capabilities[cap_def.plugin_name].remove(name)

        if name in self._dependents_graph:
            del self._dependents_graph[name]

        for dep_set in self._dependents_graph.values():
            dep_set.discard(name)

    async def invoke(self, capability: str, payload: dict, caller_plugin: str | None = None) -> Any:
        if capability not in self._capabilities:
            raise KeyError(f"Unknown capability: {capability}")
        cap_def = self._capabilities[capability]

        try:
            result = await asyncio.wait_for(cap_def.handler(payload), timeout=cap_def.timeout_seconds)
        except TimeoutError as e:
            raise TimeoutError(f"Capability {capability} timed out after {cap_def.timeout_seconds}s") from e
        return result

    def get_capability(self, name: str) -> CapabilityDefinition | None:
        return self._capabilities.get(name)

    def list_by_plugin(self, plugin_name: str) -> list[str]:
        return self._plugin_capabilities.get(plugin_name, [])

    def list_all(self) -> list[str]:
        return list(self._capabilities.keys())

    def resolve_dependencies(self, capability: str) -> list[str]:
        visited = set()
        order = []

        def dfs(cap):
            if cap in visited:
                return
            visited.add(cap)
            for dep in self._capabilities.get(
                cap, CapabilityDefinition(name=cap, plugin_name="", handler=lambda _: None)
            ).dependencies:
                dfs(dep)
            order.append(cap)

        dfs(capability)
        return order
