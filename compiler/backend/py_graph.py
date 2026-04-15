import ast
from pathlib import Path


def parse_python_file(path: Path):
    tree = ast.parse(path.read_text())
    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module.replace(".", "/") + ".py")
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.append(n.name.replace(".", "/") + ".py")

    return imports


def build_py_graph(root: str):
    root = Path(root)
    graph = {}

    for file in root.rglob("*.py"):
        rel = str(file.relative_to(root))
        graph[rel] = {"type": "python", "imports": parse_python_file(file)}

    return graph
