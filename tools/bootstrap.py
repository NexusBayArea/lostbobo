import sys
import importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def assert_imports():
    try:
        importlib.import_module("tools.runtime.tools.system_tools")
    except ImportError as e:
        print(f"[BOOTSTRAP FAIL] Import resolution failed: {e}")
        sys.exit(1)


def bootstrap():
    assert_imports()

    from tools.registry import load, validate

    print("[BOOTSTRAP] validating module map")
    validate()

    system_tools = load("system_tools")

    print("[BOOTSTRAP] executing deterministic graph")

    system_tools.register_system_tools()

    from tools.runtime.ci_compiler import compile_ci

    graph = compile_ci()
    order = graph.topo()

    for node_id in order:
        node = graph.nodes[node_id]

        print(f"[CI] {node_id}")
        rc = node.fn({})

        if rc != 0:
            print(f"[CI FAIL] {node_id}")
            return rc

    print("[CI PASS]")
    return 0


def main():
    raise SystemExit(bootstrap())


if __name__ == "__main__":
    main()
