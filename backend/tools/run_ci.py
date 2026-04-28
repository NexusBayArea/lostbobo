#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

BACKEND = Path.cwd()

STEPS = {
    "format": {"cmd": ["python", "-m", "ruff", "format", "."], "deps": []},
    "lint":   {"cmd": ["python", "-m", "ruff", "check", ".", "--fix"], "deps": ["format"]},
    "api":    {"cmd": ["python", "tools/check_api_purity.py"], "deps": ["lint"]},
    "imports":{"cmd": ["python", "tools/ci_gates/check_import_boundaries.py"], "deps": ["lint"]},
    "deps":   {"cmd": ["python", "tools/ci_gates/dependency_integrity.py"], "deps": ["lint"]},
}

def topo_run(steps):
    executed = set()
    def run_step(name):
        if name in executed: return True
        for dep in steps[name]["deps"]:
            if not run_step(dep): return False
        print(f"[CI] Running: {name}")
        result = subprocess.run(steps[name]["cmd"], cwd=BACKEND)
        if result.returncode != 0:
            print(f"[CI] FAILED: {name}")
            return False
        executed.add(name)
        return True
    for s in steps:
        if not run_step(s): sys.exit(1)
    print("[CI] All checks passed")

if __name__ == "__main__":
    topo_run(STEPS)
