import hashlib
from pathlib import Path


def file_hash(path: Path) -> str:
    """Return SHA-256 hash of file content."""
    content = path.read_bytes()
    return hashlib.sha256(content).hexdigest()
