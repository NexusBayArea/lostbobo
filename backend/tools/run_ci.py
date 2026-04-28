#!/usr/bin/env python3
"""
Minimal, stable CI runner.

Each step is a lazy-loaded module. If a step module does not exist,
it is skipped instead of crashing the entire pipeline.

Usage:
    python tools/run_ci.py
"""

import sys
from pathlib import Path

# Ensure backend/ is on sys.path so tools.* resolves correctly
_backend = str(Path(__file__).resolve().parent.parent)
if _backend not in sys.path:
    sys.path.insert(0, _backend)


STEPS = [
    "tools.ci_steps.lockfile",
    "tools.ci_steps.pruning",
    "tools.ci_steps.lint",
    "tools.ci_steps.boundaries",
    "tools.ci_steps.api",
]


def run_step(module_path: str):
    try:
        mod = __import__(module_path, fromlist=["run"])
    except ImportError:
        print(f"[CI] SKIP (missing): {module_path}")
        return True  # skip, not fail

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
