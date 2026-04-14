"""
Worker Tasks — Pure function tasks for DAG execution

RULES:
- Only (inputs, context) signature
- No global state
- No imports from app.runtime
- Must be deterministic
"""

from typing import Any, Dict


def task_a(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Simple pass-through task."""
    return {"value": 1}


def task_b(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Depends on task_a output."""
    return {"value": inputs["task_a"]["value"] + 1}


def task_multiply(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Multiply two values."""
    a = inputs.get("a", {}).get("value", 1)
    b = inputs.get("b", {}).get("value", 2)
    return {"value": a * b}


def task_sum(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Sum multiple values."""
    values = inputs.get("values", [])
    return {"value": sum(values)}
