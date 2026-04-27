import ast
import json
import sys
from pathlib import Path

ROOT = Path("backend")
GRAPH_FILE = ROOT / "tools/ci_gates/module_graph.json"


def load_graph():
    return json.loads(GRAPH_FILE.read_text())


def get_module(path: Path):
    parts = path.parts
    if "backend" not in parts:
        return None
    idx = parts.index("backend")
    if len(parts) > idx + 1:
        return parts[idx + 1]
    return None


def extract_imports(file_path: Path):
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except Exception:
        return set()
    imports = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.add(n.name.split(".")[0])

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])

    return imports


def scan():
    graph = load_graph()
    violations = []

    for py in ROOT.rglob("*.py"):
        module = get_module(py)
        if not module or module not in graph:
            continue

        allowed = set(graph[module]) | {module}
        imports = extract_imports(py)

        for imp in imports:
            if imp in graph and imp not in allowed:
                violations.append(
                    f"{py} → illegal dependency '{imp}' (allowed: {sorted(allowed)})"
                )

    return violations


if __name__ == "__main__":
    violations = scan()

    if violations:
        print("❌ Module graph violations:\n")
        for v in violations:
            print(" -", v)
        sys.exit(1)

    print("✅ Module graph locked")
