import json
from pathlib import Path
from .hash import file_hash


def parse_imports(path: Path):
    """Very naive import parser for Python files."""
    imports = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line.startswith("import "):
            imports.append(line.split()[1])
        elif line.startswith("from "):
            parts = line.split()
            if len(parts) >= 2:
                imports.append(parts[1])
    return imports


def build_graph(repo_root: str):
    """Build a simple node graph mapping node_id to node data."""
    root = Path(repo_root)
    graph = {}
    for file in root.rglob("*.py"):
        node_id = file_hash(file)
        graph[node_id] = {
            "node_id": node_id,
            "path": str(file.relative_to(root)),
            "imports": parse_imports(file),
            "dependents": [],
            "status": "new",
        }
    # Populate dependents
    for node in graph.values():
        for imp in node["imports"]:
            # naive match by module name to node path suffix
            for other in graph.values():
                if other["path"].endswith(f"{imp}.py"):
                    other["dependents"].append(node["node_id"])
    return graph
