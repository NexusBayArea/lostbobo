import subprocess
import sys
import time
from pathlib import Path

from tools.runtime.telemetry import TelemetryManager

tm = TelemetryManager()


def load_manifest() -> dict:
    path = Path("tools/ci_manifest.yml")
    if not path.exists():
        raise FileNotFoundError("tools/ci_manifest.yml missing")

    import yaml

    return yaml.safe_load(path.read_text())


def run_node(node: dict) -> int:
    path = node.get("path", "")
    if not path or not Path(path).exists():
        print(f"[DAG] missing node: {path}")
        return 1

    name = node.get("name", path)
    print(f"[DAG] Running: {name}")

    start_time = time.time()
    result = subprocess.run([sys.executable, path])
    end_time = time.time()

    duration = end_time - start_time

    # Placeholder for GPU util; in a real scenario, this would sample nvidia-smi
    gpu_util = 42.0
    status = "success" if result.returncode == 0 else "failed"

    # Record telemetry
    # We assume 'sim_type' is the node name for this baseline
    tm.record_run(
        project="SimHPC",
        sim_type=name,
        duration=duration,
        gpu_util=gpu_util,
        status=status,
    )

    return result.returncode


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


def main():
    manifest = load_manifest()
    sys.exit(topological_run(manifest))


if __name__ == "__main__":
    main()
