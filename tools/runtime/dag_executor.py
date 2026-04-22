import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from tools.runtime.contract import CONTRACTS
from tools.runtime.telemetry import TelemetryManager
from tools.runtime.trace import NodeTrace, capture_trace, run_node

tm = TelemetryManager()

TRACE_NODES: List[NodeTrace] = []


def load_manifest() -> dict:
    path = Path("tools/ci_manifest.yml")
    if not path.exists():
        raise FileNotFoundError("tools/ci_manifest.yml missing")

    import yaml

    return yaml.safe_load(path.read_text())


def run_node(node: dict, capture: bool = True) -> int:
    path = node.get("path", "")
    if not path or not Path(path).exists():
        print(f"[DAG] missing node: {path}")
        return 1

    name = node.get("name", path)
    print(f"[DAG] Running: {name}")

    start_time = time.time()

    input_data = node.get("inputs", {})

    if capture and name:
        from tools.runtime.trace import run_node as trace_run_node
        output = trace_run_node(
            name,
            lambda **kw: subprocess.run([sys.executable, path]).returncode,
            input_data,
            TRACE_NODES,
        )
        result_code = 0 if output.get("returncode", 1) == 0 else 1
    else:
        result = subprocess.run([sys.executable, path])
        result_code = result.returncode

    end_time = time.time()

    duration = end_time - start_time

    gpu_util = 42.0
    status = "success" if result_code == 0 else "failed"

    tm.record_run(
        project="SimHPC",
        sim_type=name,
        duration=duration,
        gpu_util=gpu_util,
        status=status,
    )

    return result_code


def topological_run(manifest: dict) -> int:
    nodes = manifest.get("nodes", {})
    executed = set()

    def execute(name: str) -> int:
        if name in executed:
            return 0

        node = nodes.get(name, {})

        for dep in node.get("depends_on", []):
            if execute(dep) != 0:
                return 1

        rc = run_node(node)
        executed.add(name)
        return rc

    for node_name in nodes:
        if execute(node_name) != 0:
            return 1

    return 0


def save_trace(path: str = "trace_latest.json"):
    contract = CONTRACTS.latest()
    trace = capture_trace(contract.version, TRACE_NODES)
    trace.save(path)
    print(f"[DAG] Trace saved to: {path}")


def main():
    manifest = load_manifest()
    result = topological_run(manifest)
    if result == 0:
        save_trace()
    sys.exit(result)


if __name__ == "__main__":
    main()
