import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from runtime.contract import CONTRACTS
from runtime.trace import ExecutionTrace, NodeTrace


def replay(
    trace_path: str,
    contract_version: str,
    executor: Callable[[str, dict], Any],
) -> List[Dict[str, Any]]:
    """
    Replay a saved trace under the specified contract version.
    
    Args:
        trace_path: Path to the saved ExecutionTrace JSON file
        contract_version: Version of contract to use for replay
        executor: Callable that can execute a node by name with input data
        
    Returns:
        List of replay results with expected vs actual outputs
    """
    original = ExecutionTrace.load(trace_path)
    contract = CONTRACTS.get(contract_version)

    if contract is None:
        raise ValueError(f"Unknown contract version: {contract_version}")

    results = []

    for node in original.nodes:
        try:
            actual_output = executor(node.name, node.input)
        except Exception as e:
            actual_output = {"error": str(e)}

        results.append(
            {
                "name": node.name,
                "input": node.input,
                "expected": node.output,
                "actual": actual_output,
                "status": node.status,
            }
        )

    return results


def replay_node(trace_path: str, node_name: str) -> Optional[Dict[str, Any]]:
    """
    Replay a specific node from a trace file.
    """
    original = ExecutionTrace.load(trace_path)

    for node in original.nodes:
        if node.name == node_name:
            return {
                "input": node.input,
                "output": node.output,
                "status": node.status,
                "duration_ms": node.duration_ms,
            }

    return None


def list_trace_nodes(trace_path: str) -> List[str]:
    """
    List all node names in a trace.
    """
    original = ExecutionTrace.load(trace_path)
    return [node.name for node in original.nodes]