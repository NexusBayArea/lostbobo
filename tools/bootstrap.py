from tools.runtime.tools.system_tools import register_system_tools
from tools.runtime.ci_compiler import compile_ci


def bootstrap():
    register_system_tools()

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
