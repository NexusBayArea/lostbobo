"""
Worker Entry Point — Receives task from stdin, executes, outputs result

Used by subprocess dispatch mode.
"""

import json
import sys

from worker.tasks import task_a, task_b, task_multiply, task_sum


TASK_REGISTRY = {
    "task_a": task_a,
    "task_b": task_b,
    "task_multiply": task_multiply,
    "task_sum": task_sum,
}


def main():
    payload = json.load(sys.stdin)

    task_name = payload["task"]
    inputs = payload["inputs"]
    context = payload["context"]

    if task_name not in TASK_REGISTRY:
        raise ValueError(f"Unknown task: {task_name}")

    fn = TASK_REGISTRY[task_name]
    result = fn(inputs, context)

    print(json.dumps(result))


if __name__ == "__main__":
    main()
