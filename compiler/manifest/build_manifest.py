from compiler.frontend.ts_graph import build_ts_graph
from compiler.backend.py_graph import build_py_graph
from compiler.manifest.graph import merge_graphs
from compiler.manifest.validator import validate_manifest
import json
import sys


def build_manifest(repo_root: str) -> dict:
    py_graph = build_py_graph(repo_root)
    ts_graph = build_ts_graph(repo_root)

    manifest = merge_graphs(py_graph, ts_graph)

    validate_manifest(manifest)

    return manifest


def write_manifest(manifest: dict, path="manifest.json"):
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)


if __name__ == "__main__":
    repo_root = sys.argv[1] if len(sys.argv) > 1 else "."
    manifest = build_manifest(repo_root)
    write_manifest(manifest, "manifest.json")
