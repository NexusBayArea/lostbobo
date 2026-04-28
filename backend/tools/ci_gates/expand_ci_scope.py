import json
import sys
from pathlib import Path

GRAPH = json.loads(Path("backend/tools/ci_gates/module_graph.json").read_text())


def reverse_graph(graph):
    rev = {k: set() for k in graph}
    for node, deps in graph.items():
        for d in deps:
            rev[d].add(node)
    return rev


def expand(modules):
    rev = reverse_graph(GRAPH)
    impacted = set(modules)

    stack = list(modules)

    while stack:
        m = stack.pop()
        for parent in rev.get(m, []):
            if parent not in impacted:
                impacted.add(parent)
                stack.append(parent)

    return impacted


if __name__ == "__main__":
    base = sys.argv[1].split(",") if len(sys.argv) > 1 and sys.argv[1] else []
    result = expand(base)

    print(",".join(sorted(result)))
