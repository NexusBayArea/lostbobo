from runtime.ci_compiler import compile_ci


def run_ci():
    graph = compile_ci()
    order = graph.topo()

    results = {}

    for node_id in order:
        node = graph.nodes[node_id]

        print(f"[CI] running: {node_id}")

        rc = node.fn()
        results[node_id] = rc

        if rc != 0:
            print(f"[CI FAIL] {node_id}")
            return rc

    print("[CI PASS]")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_ci())
