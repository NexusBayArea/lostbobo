import os
import sys
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT))

os.chdir(BACKEND)


STAGES = [
    {
        "name": "import_fix",
        "cmd": "python -m ruff check . --select I --fix",
        "category": "IMPORTS",
    },
    {
        "name": "format",
        "cmd": "python -m ruff format .",
        "category": "FORMAT",
    },
    {
        "name": "typing_fix",
        "cmd": "python -m ruff check . --select UP --fix",
        "category": "TYPING",
    },
    {
        "name": "strict_lint",
        "cmd": "python -m ruff check .",
        "category": "STRICT",
    },
]


def run_stage(stage):
    print(f"\n[KERNEL] Running {stage['name']}")

    result = subprocess.run(
        stage["cmd"],
        shell=True,
        capture_output=True,
        text=True,
    )

    return {
        "stage": stage["name"],
        "category": stage["category"],
        "returncode": result.returncode,
        "stdout": result.stdout[-2000:] if result.stdout else "",
        "stderr": result.stderr[-2000:] if result.stderr else "",
    }


def run_kernel():
    trace = []

    print("[KERNEL] boot sequence start")

    for stage in STAGES:
        result = run_stage(stage)
        trace.append(result)

        print(f"[KERNEL] {result['stage']}: {result['returncode']}")

        if stage["name"] == "strict_lint" and result["returncode"] != 0:
            print("[KERNEL] FAILED at strict gate")
            break

    with open("ci_trace.json", "w") as f:
        json.dump(trace, f, indent=2)

    if trace[-1]["returncode"] == 0:
        print("\n[KERNEL] SUCCESS - system converged")
        return 0

    print("\n[KERNEL] FAILED - non-converged state")
    return 1


if __name__ == "__main__":
    raise SystemExit(run_kernel())