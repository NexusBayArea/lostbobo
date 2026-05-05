import asyncio
import time

from backend.runtime.contract import CONTRACT
from backend.runtime.graph import GRAPH
from backend.runtime.trace import NodeTrace, capture_trace, ExecutionTrace


async def execute_node(node_id: str) -> dict:
    """Execute a single DAG node with timing and tracing."""
    start = time.time()
    node = GRAPH.get(node_id)

    try:
        if asyncio.iscoroutinefunction(node.fn):
            result = await node.fn()
        else:
            result = node.fn()

        status = "success"
        output = result if isinstance(result, dict) else {"status": "ok", "result": result}
    except Exception as e:
        status = "failed"
        output = {"error": str(e)}
        raise

    duration = (time.time() - start) * 1000

    return {
        "node_id": node_id,
        "status": status,
        "duration_ms": duration,
        "output": output,
    }


async def execute_dag() -> ExecutionTrace:
    """Execute the full DAG with full tracing."""
    print(f"Executing DAG under contract {CONTRACT.version}")

    order = GRAPH.topological_sort()
    trace_nodes = []

    for node_id in order:
        print(f"Running node: {node_id}")
        result = await execute_node(node_id)
        trace_nodes.append(
            NodeTrace(
                name=node_id,
                input={},
                output=result["output"],
                status=result["status"],
                duration_ms=result["duration_ms"],
            )
        )

    trace = capture_trace(
        contract_version=CONTRACT.version,
        nodes=trace_nodes,
        edges=[],
        manifest_hash="current",
    )

    trace.save("trace_latest.json")
    print("DAG execution completed. Trace saved.")
    return trace