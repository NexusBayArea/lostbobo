import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def bootstrap():
    from tools.runtime.tools.system_tools import register_system_tools
    from tools.runtime.tool_registry import TOOL_REGISTRY
    from tools.runtime.ci_compiler import compile_ci

    register_system_tools()
    graph = compile_ci()
    order = graph.topo()

    results = {}

    for node_id in order:
        node = graph.nodes[node_id]
        print(f"[CI] {node_id}")

        rc = node.fn({})
        results[node_id] = rc

        if rc != 0:
            print(f"[CI FAIL] {node_id}")
            return rc

    print("[CI PASS]")
    return 0


def main():
    bootstrap()


if __name__ == "__main__":
    main()
