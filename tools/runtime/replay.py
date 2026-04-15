import json
import sys
import subprocess
from pathlib import Path
from tools.runtime.contract import CONTRACT

CONTRACT.apply()
TRACE_FILE = CONTRACT.root / "runtime_trace.json"


def load_trace():
    if not TRACE_FILE.exists():
        print("[REPLAY] No trace file found")
        sys.exit(1)

    return json.loads(TRACE_FILE.read_text())


def replay(full: bool = False):
    trace = load_trace()
    nodes = trace["nodes"]

    for name, node in nodes.items():
        if not full and node["status"] == "success":
            continue

        cmd = node.get("command")

        if not cmd:
            print(f"[SKIP] {name} (no command recorded)")
            continue

        print(f"[REPLAY] {name}")
        result = subprocess.run(cmd)

        if result.returncode != 0:
            print(f"[FAIL] {name}")
            sys.exit(result.returncode)

    print("[REPLAY] complete")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "failed"

    if mode == "full":
        replay(full=True)
    else:
        replay(full=False)
