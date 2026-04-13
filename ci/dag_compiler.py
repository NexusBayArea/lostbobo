#!/usr/bin/env python3
"""DAG Compiler - outputs jobs for execution engine."""

import json
import subprocess


def load_module_graph():
    try:
        with open("ci/module_graph.json") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "core": {"paths": ["app/core"], "deps": []},
            "api": {"paths": ["app/api"], "deps": ["core"]},
            "worker": {"paths": ["worker", "app/services/worker"], "deps": ["core"]},
        }


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


def compute_dag(base="origin/main", head="HEAD"):
    graph = load_module_graph()
    files = get_changed_files(base, head)

    if not files:
        modules = set(graph.keys())
    else:
        affected = match_modules(files, graph)
        modules = expand_deps(affected, graph)

    order = topo_sort(graph)

    jobs = []
    for module in order:
        if module not in modules:
            continue

        deps = graph.get(module, {}).get("deps", [])

        jobs.append(
            {
                "name": module,
                "inputs": graph.get(module, {}).get("paths", []),
                "deps": deps,
                "entry": f"ci/jobs/{module}.py",
            }
        )

    policy_nodes = [
        {
            "name": "no_mutable_tags",
            "rule": "immutable_image_tags",
            "inputs": [".github/workflows"]
        },
        {
            "name": "dag_validity",
            "rule": "dag_integrity",
            "inputs": ["ci/dag.json"]
        }
    ]

    return {
        "policy_nodes": policy_nodes,
        "compute_nodes": jobs
    }


def main():
    import sys
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--output", help="Output file path")
    args = parser.parse_args()

    dag = compute_dag(args.base, args.head)
    output = json.dumps(dag, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
    else:
        print(output)


if __name__ == "__main__":
    main()
