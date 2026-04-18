# Simple DAG utilities


def topological_sort(graph):
    """Return nodes in topological order using Kahn's algorithm."""
    in_degree = {nid: 0 for nid in graph}
    for node in graph.values():
        for dep in node.get("imports", []):
            # map import name to node id if present
            for other in graph.values():
                if other["path"].endswith(f"{dep}.py"):
                    in_degree[other["node_id"]] += 1
    queue = [nid for nid, deg in in_degree.items() if deg == 0]
    order = []
    while queue:
        n = queue.pop()
        order.append(n)
        for dependent in graph[n].get("dependents", []):
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)
    return order
