"""
Executor — Plan-based deterministic execution engine

Executes precompiled ExecutionPlan with fixed order and dependencies.
"""

from typing import Any, Dict

from app.runtime.plan import ExecutionPlan


class Executor:
    def __init__(self, plan: ExecutionPlan):
        self.plan = plan
        self.plan.validate()
        self.results: Dict[str, Any] = {}

    def run(self, dispatch: Any, context: Dict[str, Any] = None) -> Dict[str, Any]:
        context = context or {}

        for name in self.plan.order:
            deps = self.plan.dependencies[name]

            inputs = {dep: self.results[dep] for dep in deps}

            payload = self.plan.payloads[name]
            node = type(
                "Node", (), {"fn": payload.get("fn"), "name": payload.get("name")}
            )()

            self.results[name] = dispatch(node, inputs, context)

        return self.results
