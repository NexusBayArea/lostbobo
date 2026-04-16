import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def bootstrap():
    from tools.registry import validate

    print("[BOOTSTRAP] validating module map")
    validate()

    print("[BOOTSTRAP] executing deterministic graph")

    from tools.runtime.nodes import register_default_nodes
    from tools.runtime.graph import GRAPH

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


def main():
    raise SystemExit(bootstrap())


if __name__ == "__main__":
    main()
