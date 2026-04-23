import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union


def normalize_output(output: Any) -> Any:
    """
    Normalize output for deterministic comparison.
    Handles floats, dicts, lists, and other comparable types.
    """
    if output is None:
        return None

    if isinstance(output, dict):
        return {k: normalize_output(v) for k, v in sorted(output.items())}

    if isinstance(output, list):
        return [normalize_output(v) for v in output]

    if isinstance(output, float):
        return round(output, 10)

    return output


def compare_values(expected: Any, actual: Any) -> bool:
    """
    Compare two values with normalization for deterministic results.
    """
    return normalize_output(expected) == normalize_output(actual)


def diff_nodes(replayed_nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Compare expected vs actual outputs for each node.
    
    Args:
        replayed_nodes: List of node replay results from backend.tools.runtime.replay.replay()
        
    Returns:
        List of diffs (empty if no differences)
    """
    diffs = []

    for node in replayed_nodes:
        expected = node.get("expected", {})
        actual = node.get("actual", {})

        if not compare_values(expected, actual):
            diffs.append(
                {
                    "node": node["name"],
                    "input": node.get("input"),
                    "expected": expected,
                    "actual": actual,
                    "status": node.get("status"),
                }
            )

    return diffs


def diff_trace(
    trace_path: str,
    executor: Callable[[str, dict], Any],
    contract_version: str = "v1",
) -> List[Dict[str, Any]]:
    """
    Load trace, replay, and diff in one call.
    
    Args:
        trace_path: Path to saved ExecutionTrace JSON
        executor: Callable that executes a node
        contract_version: Contract version to use
        
    Returns:
        List of diffs (empty if no differences)
    """
    from backend.tools.runtime.replay import replay

    replayed = replay(trace_path, contract_version, executor)
    return diff_nodes(replayed)


def save_diff_report(diffs: List[Dict[str, Any]], output_path: str):
    """
    Save diff report to JSON file.
    """
    with open(output_path, "w") as f:
        json.dump(diffs, f, indent=2)


def load_diff_report(input_path: str) -> List[Dict[str, Any]]:
    """
    Load diff report from JSON file.
    """
    with open(input_path) as f:
        return json.load(f)


def format_diffs(diffs: List[Dict[str, Any]]) -> str:
    """
    Format diffs for human-readable output.
    """
    if not diffs:
        return "No differences detected"

    lines = []
    for d in diffs:
        lines.append(f"Node: {d['node']}")
        lines.append(f"  Expected: {json.dumps(d['expected'], indent=4)}")
        lines.append(f"  Actual:   {json.dumps(d['actual'], indent=4)}")
        lines.append("")

    return "\n".join(lines)