import hashlib
from pathlib import Path


def hash_file(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hash_string(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def compute_node_signature(node: dict, dep_signatures: list[str]) -> str:
    path = Path(node.get("path", ""))

    code_hash = hash_file(path)

    combined = code_hash + "".join(dep_signatures)

    return hash_string(combined)
