#!/usr/bin/env python3
"""
Unified Deterministic CI runner with topological DAG execution and content-addressed caching.

Usage:
    python tools/run_ci.py
"""
import sys
import subprocess
from pathlib import Path

from tools.ci.cache import node_hash, load_cache, save_cache
from tools.ci.detect_changes import git_changed_files, classify

# When called with working-directory: backend in CI,
# cwd IS the backend directory already.
BACKEND = Path.cwd()


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
            "meta": m,
            "run": mod.run,
            "deps": m.get("deps", []),
        }
    return steps


def execute_dag_fused(steps):
    completed = {}
    failed = set()

    while len(completed) + len(failed) < len(steps):
        ready = [
            name for name, s in steps.items()
            if name not in completed
            and name not in failed
            and all(dep in completed for dep in s["deps"])
        ]

        if not ready:
            raise RuntimeError("Deadlock in DAG")

        for name in ready:
            step = steps[name]
            dep_hashes = [completed[d] for d in step["deps"]]
            current_hash = node_hash(step, dep_hashes)
            cached_hash = load_cache(name)

            if cached_hash == current_hash:
                print(f"[CI] SKIP (cache hit): {name}")
                completed[name] = current_hash
                continue

            print(f"[CI] RUN: {name}")
            ok = step["run"]()

            if not ok:
                print(f"[CI] FAIL: {name}")
                failed.add(name)
                continue

            save_cache(name, current_hash)
            completed[name] = current_hash
            print(f"[CI] PASS: {name}")

        if failed:
            break

    return failed


def main():
    # Load plugins
    STEP_MODULES = [
        "tools.ci_steps.lockfile",
        "tools.ci_steps.pruning",
        "tools.ci_steps.lint",
        "tools.ci_steps.boundaries",
        "tools.ci_steps.api",
    ]
    steps = load_steps(STEP_MODULES)

    # Execute DAG with caching
    failed = execute_dag_fused(steps)

    if failed:
        print(f"\n[CI] Failed steps: {failed}")
        sys.exit(1)

    print("\n[CI] All checks passed")


if __name__ == "__main__":
    main()
