name: detect_changes.py

#!/usr/bin/env python3
"""
CI Change Detection Engine.

Loads module graph, detects changed files, computes affected modules with dependency closure.
"""

import json
import subprocess
import sys

GRAPH_PATH = "ci/module_graph.json"
ALL_MODULES = "core,api,worker,autoscaler,tests,scripts,docker,ci"


def load_graph():
    try:
        with open(GRAPH_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def get_changed_files(base="origin/main", head="HEAD"):
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{base}...{head}"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return []
        return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
    except Exception:
        return []


def match_modules(files, graph):
    affected = set()
    for f in files:
        for module, data in graph.items():
            for path in data.get("paths", []):
                if f.startswith(path):
                    affected.add(module)
                    break
    return affected


def expand_deps(modules, graph):
    expanded = set(modules)

    def visit(m):
        for dep in graph.get(m, {}).get("deps", []):
            if dep not in expanded:
                expanded.add(dep)
                visit(dep)

    for m in list(modules):
        visit(m)

    return expanded


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "origin/main"
    head = sys.argv[2] if len(sys.argv) > 2 else "HEAD"

    graph = load_graph()
    files = get_changed_files(base, head)

    if not files:
        print(ALL_MODULES)
        return

    affected = match_modules(files, graph)
    if not affected:
        print(ALL_MODULES)
        return

    full = expand_deps(affected, graph)
    print(",".join(sorted(full)))


if __name__ == "__main__":
    main()
