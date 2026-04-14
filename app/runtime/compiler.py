"""
DAG Compiler — Validates and compiles DAG into deterministic execution plan

Separates DAG definition (input) from execution plan (artifact).
"""

from app.runtime.plan import ExecutionPlan
from app.runtime.scheduler import topological_sort


def compile_dag(dag) -> ExecutionPlan:
    dag.validate()

    order = topological_sort(dag.nodes)

    dependencies = {}
    payloads = {}

    for name, node in dag.nodes.items():
        dependencies[name] = node.deps
        payloads[name] = {"fn": node.fn, "name": node.name}

    plan = ExecutionPlan(
        order=order,
        dependencies=dependencies,
        payloads=payloads,
    )

    plan.validate()

    return plan


def serialize_plan(plan: ExecutionPlan) -> dict:
    return {
        "order": plan.order,
        "dependencies": plan.dependencies,
        "payloads": {
            name: {
                "fn_name": payload.get(
                    "fn_name",
                    payload.get("fn", "").__name__ if payload.get("fn") else "",
                )
            }
            for name, payload in plan.payloads.items()
        },
    }
