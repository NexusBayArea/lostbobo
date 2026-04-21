from pathlib import Path

from ..cache.store import cache_get, cache_set
from ..core.hash import file_hash


def parse_imports(path: Path):
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


def process_file(path: Path):
    node_id = file_hash(path)
    cached = cache_get(node_id)
    if cached:
        return cached
    imports = parse_imports(path)
    node = {
        "node_id": node_id,
        "path": str(path),
        "imports": imports,
        "status": "pending",
    }
    cache_set(node_id, node)
    return node
