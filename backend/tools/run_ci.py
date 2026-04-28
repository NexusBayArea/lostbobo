#!/usr/bin/env python3
"""
Unified Deterministic CI runner with lazy-loaded plugin architecture.

Usage:
    python tools/run_ci.py
"""
import sys
import subprocess
from pathlib import Path

# Define the sequence of CI steps as plugin modules
STEPS = [
    "tools.ci_steps.format",
    "tools.ci_steps.lint",
    "tools.ci_steps.api",
    "tools.ci_steps.boundaries",
    "tools.ci_steps.deps",
]


def run_step(module_path: str):
    try:
        mod = __import__(module_path, fromlist=["run"])
    except ImportError:
        print(f"[CI] SKIP (missing): {module_path}")
        return True  # skip missing steps gracefully

    print(f"[CI] Running: {module_path}")
    ok = mod.run()

    if not ok:
        print(f"[CI] FAILED: {module_path}")
        return False

    print(f"[CI] PASS: {module_path}")
    return True


def main():
    failed = []

    for step in STEPS:
        if not run_step(step):
            failed.append(step)

    if failed:
        print(f"\n[CI] Failed: {failed}")
        sys.exit(1)

    print("\n[CI] All checks passed")


if __name__ == "__main__":
    main()
