import re
from pathlib import Path

IMPORT_RE = re.compile(r"from\s+['\"](.+?)['\"]")


def parse_ts_file(path: Path):
    imports = []
    for line in path.read_text().splitlines():
        match = IMPORT_RE.search(line)
        if match:
            imports.append(match.group(1))
    return imports


def build_ts_graph(root: str):
    root = Path(root)
    graph = {}

    for file in root.rglob("*.ts"):
        rel = str(file.relative_to(root))
        graph[rel] = {"type": "typescript", "imports": parse_ts_file(file)}

    return graph
