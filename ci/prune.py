def prune_dag(dag_nodes, failed_node_names):
    """
    Inputs:
        dag_nodes: List of all nodes in the DAG.
        failed_node_names: Names of nodes that failed.
    Returns:
        A pruned list of nodes consisting of failed nodes and their downstream dependents.
    """
    affected = set(failed_node_names)
    
    # We need to find all nodes that depend directly or indirectly on failed nodes
    # We iterate until we reach convergence (stable set)
    changed = True
    while changed:
        before_count = len(affected)
        for node in dag_nodes:
            # If any dependency of this node is in the affected set, this node is affected
            if any(dep in affected for dep in node.get("deps", [])):
                affected.add(node["name"])
        changed = len(affected) > before_count

    return [n for n in dag_nodes if n["name"] in affected]
