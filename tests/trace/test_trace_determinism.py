import pytest

from app.runtime.executor import execute_plan
from app.runtime.compiler import compile_dag
from app.runtime.trace import TraceCollector


def build_test_dag():
    # keep this SIMPLE and deterministic
    return {
        "nodes": {
            "a": {"op": "const", "value": 1},
            "b": {"op": "const", "value": 2},
            "c": {"op": "add", "inputs": ["a", "b"]},
        }
    }


def run_with_trace(dag):
    plan = compile_dag(dag)

    trace = TraceCollector()
    result = execute_plan(plan, trace=trace)

    return result, trace.events


def normalize(trace):
    normalized = []

    for event in trace:
        normalized.append({
            "node": event.get("node"),
            "status": event.get("status"),
            "inputs": event.get("inputs"),
            "outputs": event.get("outputs"),
        })

    return normalized


@pytest.mark.trace
def test_trace_determinism():
    dag = build_test_dag()

    result1, trace1 = run_with_trace(dag)
    result2, trace2 = run_with_trace(dag)

    assert result1 == result2, "Results differ"

    # Core check
    assert normalize(trace1) == normalize(trace2), "Trace is not deterministic"
