"""
Executor — Core runtime engine for DAG execution

Runs nodes in topological order, passing outputs as inputs to dependent nodes.
"""

from typing import Any, Dict

from app.runtime.dag import DAG
from app.runtime.scheduler import topological_sort


class Executor:
    def __init__(self, dag: DAG):
        self.dag = dag
        self.results: Dict[str, Any] = {}

    def run(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        context = context or {}
        self.dag.validate()

        order = topological_sort(self.dag.nodes)

        for name in order:
            node = self.dag.nodes[name]

            inputs = {dep: self.results[dep] for dep in node.deps}

            self.results[name] = node.fn(inputs, context)

        return self.results
