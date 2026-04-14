"""
Executor — Plan-based deterministic execution engine with tracing

Executes precompiled ExecutionPlan with fixed order and dependencies.
Records trace events for every node execution.
"""

from typing import Any, Dict
import time
import uuid

from app.runtime.plan import ExecutionPlan
from app.runtime.trace import TraceEvent, TraceBuffer


class Executor:
    def __init__(self, plan: ExecutionPlan):
        self.plan = plan
        self.plan.validate()
        self.results: Dict[str, Any] = {}
        self.trace = TraceBuffer()

    def run(self, dispatch: Any, context: Dict[str, Any] = None) -> Dict[str, Any]:
        context = context or {}

        for name in self.plan.order:
            deps = self.plan.dependencies[name]

            inputs = {dep: self.results[dep] for dep in deps}

            payload = self.plan.payloads[name]
            node = type(
                "Node", (), {"fn": payload.get("fn"), "name": payload.get("name")}
            )()

            start = time.time()

            try:
                output = dispatch(node, inputs, context)
                status = "success"
                error = None
            except Exception as e:
                output = {"error": str(e)}
                status = "failed"
                error = str(e)

            end = time.time()

            self.results[name] = output

            self.trace.record(
                TraceEvent(
                    trace_id=str(uuid.uuid4()),
                    node=name,
                    inputs=inputs,
                    outputs=output,
                    start_ms=start * 1000,
                    end_ms=end * 1000,
                    duration_ms=(end - start) * 1000,
                    status=status,
                    error=error,
                )
            )

        return self.results
