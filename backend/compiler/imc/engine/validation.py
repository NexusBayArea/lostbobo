def invalidate(node_id, graph):
    """Return set of dependent node ids affected by change to node_id."""
    affected = set()
    queue = [node_id]
    while queue:
        current = queue.pop()
        for dependent in graph.get(current, {}).get("dependents", []):
            if dependent not in affected:
                affected.add(dependent)
                queue.append(dependent)
    return affected
