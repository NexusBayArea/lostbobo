import subprocess
from pathlib import Path


def run():
    gate = Path("tools/ci_gates/dependency_integrity.py")
    if not gate.exists():
        print("[deps] Gate script not found, skipping")
        return True
    return subprocess.run(["python", str(gate)]).returncode == 0
