from tools.registry import load, validate


def bootstrap():
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


if __name__ == "__main__":
    raise SystemExit(bootstrap())
