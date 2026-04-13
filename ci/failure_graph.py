def build_failure_graph(failures):
    """Organizes failures by node for analysis."""
    graph = {}
    for f in failures:
        graph[f["node"]] = {
            "error": f.get("error_type", "unknown"),
            "inputs": f.get("inputs", []),
            "context": f
        }
    return graph
