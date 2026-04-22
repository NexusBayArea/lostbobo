import subprocess
import json
import time
import sys
from pathlib import Path
from tools.ci.dag import CI_DAG

TRACE = []


def run_node(node, cwd=None):
    print(f"\n[TRACE] Running {node.get('name', node['id'])}")

    start = time.time()

    result = subprocess.run(
        node["cmd"],
        shell=True,
        capture_output=True,
        text=True,
        cwd=cwd,
    )

    duration = time.time() - start

    entry = {
        "node": node["id"],
        "name": node.get("name", node["id"]),
        "cmd": node["cmd"],
        "return_code": result.returncode,
        "stdout": result.stdout[-5000:] if result.stdout else "",
        "stderr": result.stderr[-5000:] if result.stderr else "",
        "duration": round(duration, 3),
        "status": "PASS" if result.returncode == 0 else "FAIL",
    }

    TRACE.append(entry)

    print(f"[TRACE] {entry['status']} - {entry['duration']}s")

    if result.returncode != 0:
        print(f"[TRACE] STDERR: {result.stderr[-1000:]}")
        return False

    return True


def run_dag(cwd=None):
    for node in CI_DAG:
        success = run_node(node, cwd=cwd)
        if not success:
            print(f"\n[TRACE] FAILED at node: {node.get('name', node['id'])}")
            save_trace()
            sys.exit(1)

    save_trace()
    print("\n[TRACE] CI completed successfully")
    return True


def save_trace(path="ci_trace.json"):
    with open(path, "w") as f:
        json.dump(TRACE, f, indent=2)
    print(f"[TRACE] Saved to {path}")


def load_trace(path="ci_trace.json"):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return None


if __name__ == "__main__":
    try:
        run_dag()
    except Exception as e:
        save_trace()
        print(f"[TRACE] Exception: {e}")
        raise
