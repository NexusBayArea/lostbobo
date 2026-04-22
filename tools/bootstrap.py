import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def bootstrap():
    from tools import registry
    from tools.runtime.tools import system_tools

    print("[BOOTSTRAP] validating module map")
    registry.validate()

    print("[BOOTSTRAP] registering system tools")
    # Fix: Pass the registry to satisfy the positional argument requirement
    system_tools.register_system_tools(registry)

    print("[BOOTSTRAP] executing deterministic graph")
    from tools.runtime.graph import GRAPH
    from tools.runtime.nodes import register_default_nodes

    register_default_nodes()
    order = GRAPH.topologically_sorted()

    for node_id in order:
        node = GRAPH.get(node_id)
        print(f"[CI] {node_id}")
        rc = node.fn({})
        if rc != 0:
            print(f"[CI FAIL] {node_id}")
            return rc

    print("[CI PASS]")
    return 0


if __name__ == "__main__":
    raise SystemExit(bootstrap())
