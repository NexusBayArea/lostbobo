#!/usr/bin/env python3
"""
Unified Deterministic CI runner.

Usage:
    python tools/run_ci.py
"""

import sys
import subprocess
from pathlib import Path

# When called with working-directory: backend in CI,
# cwd IS the backend directory already.
BACKEND = Path.cwd()

# Define the DAG of CI steps
STEPS = {
    "format": {
        "cmd": ["python", "-m", "ruff", "format", "--check", "."],
        "deps": [],
    },
    "lint": {
        "cmd": ["python", "-m", "ruff", "check", "."],
        "deps": ["format"],
    },
    "api": {
        "cmd": ["python", "tools/check_api_purity.py"],
        "deps": ["lint"],
    },
    "imports": {
        "cmd": ["python", "tools/ci_gates/check_import_boundaries.py"],
        "deps": ["lint"],
    },
    "deps": {
        "cmd": ["python", "tools/ci_gates/dependency_integrity.py"],
        "deps": ["lint"],
    },
}


def topo_run(steps):
    executed = set()

    def run_step(name):
        if name in executed:
            return True

        step = steps[name]

        for dep in step["deps"]:
            if not run_step(dep):
                return False

        print(f"[CI] Running: {name}")
        # Run from BACKEND as cwd is managed by workflow
        result = subprocess.run(step["cmd"], cwd=BACKEND)

        if result.returncode != 0:
            print(f"[CI] FAILED: {name}")
            return False

        executed.add(name)
        return True

    for s in steps:
        if not run_step(s):
            sys.exit(1)

    print("[CI] All steps passed")


if __name__ == "__main__":
    topo_run(STEPS)
