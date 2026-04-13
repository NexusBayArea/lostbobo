#!/usr/bin/env python3
"""
DAG Execution Planner.

Topologically sorts modules and outputs execution order for affected modules.
"""

import json
import sys

GRAPH_PATH = "ci/module_graph.json"


def load_graph():
    try:
        with open(GRAPH_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def topo_sort(graph):
    visited = set()
    order = []

    def visit(node):
        if node in visited:
            return
        visited.add(node)
        for dep in graph.get(node, {}).get("deps", []):
            visit(dep)
        order.append(node)

    for node in graph:
        visit(node)

    return order


def main():
    graph = load_graph()
    affected = set(sys.argv[1].split(",")) if len(sys.argv) > 1 else set()

    if not affected:
        print("[]")
        return

    order = topo_sort(graph)
    execution = [m for m in order if m in affected]

    print(json.dumps(execution))


if __name__ == "__main__":
    main()
