import os
import sys
from pathlib import Path

# Force the project root (C:\Users\arche\SimHPC) into sys.path
# and specifically backend/ to ensure consistent import resolution
ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT))

import subprocess

def run(cmd: str):
    print(f"[KERNEL] {cmd}")
    return subprocess.run(cmd, shell=True).returncode

def run_kernel():
    print("[KERNEL] boot sequence start")

    # Final strict validation
    code = run("python -m ruff check .")

    if code != 0:
        print("[KERNEL] FAILED - validation failed")
        return 1

    print("[KERNEL] SUCCESS - validation passed")
    return 0

if __name__ == "__main__":
    raise SystemExit(run_kernel())

