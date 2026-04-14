"""
Dispatch Layer — Single control point for all execution

Routes DAG node execution to different backends:
- local: direct function call
- subprocess: isolated child process
"""

import json
import subprocess
from typing import Any, Dict


def dispatch(
    node: Any, inputs: Dict[str, Any], context: Dict[str, Any]
) -> Dict[str, Any]:
    mode = context.get("mode", "local")

    if mode == "local":
        return node.fn(inputs, context)
    elif mode == "subprocess":
        return run_subprocess(node.name, inputs, context)
    else:
        raise ValueError(f"Unknown dispatch mode: {mode}")


def run_subprocess(
    task_name: str, inputs: Dict[str, Any], context: Dict[str, Any]
) -> Dict[str, Any]:
    payload = {
        "task": task_name,
        "inputs": inputs,
        "context": context,
    }

    result = subprocess.run(
        ["python", "-m", "worker.entry"],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Task {task_name} failed: {result.stderr}")

    return json.loads(result.stdout)
