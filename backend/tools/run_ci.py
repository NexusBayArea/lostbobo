#!/usr/bin/env python3
"""
Unified Deterministic CI runner with topological DAG execution.

Usage:
    python tools/run_ci.py
"""
import sys
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Define the sequence of CI steps as plugin modules
STEP_MODULES = [
    "tools.ci_steps.lockfile",
    "tools.ci_steps.pruning",
    "tools.ci_steps.lint",
    "tools.ci_steps.boundaries",
    "tools.ci_steps.api",
]


def load_steps(step_paths):
    steps = {}
    for path in step_paths:
        try:
            mod = __import__(path, fromlist=["meta", "run"])
        except ImportError:
            print(f"[CI] SKIP (missing): {path}")
            continue

        m = mod.meta()
        steps[m["name"]] = {
            "run": mod.run,
            "deps": m.get("deps", []),
        }
    return steps


def topo_sort(steps):
    visited = set()
    order = []

    def visit(node):
        if node in visited:
            return
        visited.add(node)
        for dep in steps[node]["deps"]:
            if dep not in steps:
                raise RuntimeError(f"Missing dependency: {dep}")
            visit(dep)
        order.append(node)

    for node in steps:
        visit(node)
    return order


def execute_dag(steps):
    completed = set()
    failed = set()

    while len(completed) + len(failed) < len(steps):
        ready = [
            name for name, s in steps.items()
            if name not in completed
            and name not in failed
            and all(dep in completed for dep in s["deps"])
        ]

        if not ready:
            raise RuntimeError("Deadlock in CI DAG (cycle or missing dep)")

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(steps[name]["run"]): name for name in ready}

            for future in as_completed(futures):
                name = futures[future]
                ok = future.result()

                if ok:
                    print(f"[CI] PASS: {name}")
                    completed.add(name)
                else:
                    print(f"[CI] FAIL: {name}")
                    failed.add(name)

        if failed:
            break

    return failed


def main():
    steps = load_steps(STEP_MODULES)
    print("[CI] Execution plan:", topo_sort(steps))

    failed = execute_dag(steps)

    if failed:
        print(f"\n[CI] Failed steps: {failed}")
        sys.exit(1)

    print("\n[CI] All checks passed")


if __name__ == "__main__":
    main()
