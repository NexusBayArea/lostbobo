import sys
import subprocess
from pathlib import Path
from tools.runtime.contract import CONTRACT
from tools.runtime.capabilities import CAPABILITIES
from tools.runtime.trace import Trace

def get_state_handlers():
    from tools.runtime.capabilities import CAPABILITIES

    if not CAPABILITIES.get("state") or not CAPABILITIES["state"].enabled:
        return None, None

    try:
        from tools.runtime.state import load_state, save_state
        return load_state, save_state
    except ImportError:
        print("[WARN] state capability enabled but module missing")
        return None, None

CONTRACT.apply()

PYPROJECT = CONTRACT.root / "pyproject.toml"
LOCKFILE = CONTRACT.root / "requirements.lock"
MANIFEST = CONTRACT.root / "tools" / "ci_manifest.yml"


def read_lock() -> set[str]:
    if not LOCKFILE.exists():
        raise RuntimeError("Missing requirements.lock")

    return {
        line.strip()
        for line in LOCKFILE.read_text().splitlines()
        if line.strip() and "==" in line
    }


def verify_capabilities():
    print("[KERNEL] capability validation")
    for cap in CAPABILITIES.values():
        if not cap.enabled:
            continue
        missing = [p for p in cap.required_files if not Path(p).exists()]
        if missing:
            print(f"[FAIL] capability '{cap.name}' missing files:")
            for m in missing:
                print(" ", m)
            sys.exit(1)
    print("[PASS] capabilities valid")


def validate_lock_format() -> bool:
    """Validate lockfile has correct format with pinned versions."""
    if not LOCKFILE.exists():
        print("[FAIL] requirements.lock not found")
        return False

    content = LOCKFILE.read_text()
    lines = content.splitlines()

    pinned = [line.strip() for line in lines if line.strip() and "==" in line]

    if not pinned:
        print("[FAIL] no pinned dependencies found in lockfile")
        return False

    unpinned = [line for line in pinned if "==" not in line]
    if unpinned:
        print(f"[FAIL] found {len(unpinned)} unpinned dependencies")
        return False

    print(f"[KERNEL] lockfile validated: {len(pinned)} pinned deps")
    return True


def validate_dependencies():
    print("[KERNEL] dependency validation")

    if not PYPROJECT.exists():
        print("[FAIL] pyproject.toml not found")
        sys.exit(1)

    if not validate_lock_format():
        sys.exit(1)

    print("[PASS] dependency kernel clean")


def validate_import(path: str) -> bool:
    p = Path(path)
    if p.exists():
        return True
    alt = CONTRACT.root / path
    if alt.exists():
        return True
    print(f"[FAIL] missing module: {path}")
    return False


def load_manifest():
    import yaml

    return yaml.safe_load(MANIFEST.read_text())


def run_node(name: str, node: dict, trace: Trace) -> int:
    path = node.get("path", "")

    if not validate_import(path):
        trace.start_node(name)
        trace.end_node(name, False)
        return 1

    trace.start_node(name)

    cmd = [sys.executable, path]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    trace.end_node(name, result.returncode == 0, result)

    return result.returncode


def execute_dag(manifest: dict, trace: Trace):
    nodes = manifest.get("nodes", {})

    executed = set()

    def run(name: str) -> int:
        if name in executed:
            return 0

        node = nodes[name]

        for dep in node.get("depends_on", []):
            if run(dep) != 0:
                return 1

        rc = run_node(name, node, trace)
        executed.add(name)
        return rc

    for name in nodes:
        if run(name) != 0:
            return 1

    return 0


def self_heal():

def validate_contract():
    print("[KERNEL] contract validation")
    required_attrs = ["root", "paths"]
    for attr in required_attrs:
        if not hasattr(CONTRACT, attr):
            print(f"[FAIL] contract missing attribute: {attr}")
            sys.exit(1)
    print("[PASS] contract valid")
    print("[KERNEL] self-heal phase")

    required = [
        "tools/deps/verify_fingerprint.py",
        "tools/deps/dependency_scan.py",
        "tools/ci_gates/system_contract.py",
    ]

    missing = [p for p in required if not Path(p).exists()]

    if missing:
        print("[FAIL] missing kernel modules:")
        for m in missing:
            print(" ", m)
        sys.exit(1)

    print("[PASS] kernel integrity complete")


def main():
    print("[KERNEL] boot sequence start")

    trace = Trace()
    verify_capabilities()
    validate_dependencies()
self_heal()
    validate_contract()

    manifest = load_manifest()
    rc = execute_dag(manifest, trace)
    trace.save()

    if rc != 0:
        print(f"[FAIL] DAG execution failed with code {rc}")
        sys.exit(rc)

    print("[KERNEL] boot sequence complete")


if __name__ == "__main__":
    main()
