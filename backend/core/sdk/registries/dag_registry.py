from __future__ import annotations


class DAGRegistry:
    def __init__(self):
        self._nodes = {}

    def register_node(self, node_type: str, executor, plugin_name: str):
        self._nodes[node_type] = {
            "executor": executor,
            "plugin": plugin_name,
        }

    def get_executor(self, node_type: str):
        entry = self._nodes.get(node_type)
        return entry["executor"] if entry else None
