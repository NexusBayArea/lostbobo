import fnmatch
import hashlib
import subprocess
from pathlib import Path

CACHE_DIR = Path(".ci_cache")
CACHE_DIR.mkdir(exist_ok=True)


def hash_files(patterns: list[str]) -> str:
    h = hashlib.sha256()
    for pattern in patterns:
        for p in sorted(Path(".").rglob("*")):
            if fnmatch.fnmatch(str(p), pattern) and p.is_file():
                h.update(p.read_bytes())
    return h.hexdigest()


def hash_tools(tools: list[str]) -> str:
    h = hashlib.sha256()
    for tool in tools:
        try:
            out = subprocess.check_output(["python", "-m", tool, "--version"], text=True)
        except Exception:
            out = "unknown"
        h.update(out.encode())
    return h.hexdigest()


def node_hash(step: dict, dep_hashes: list[str]) -> str:
    h = hashlib.sha256()
    h.update(hash_files(step["meta"].get("inputs", [])).encode())
    for d in sorted(dep_hashes):
        h.update(d.encode())
    h.update(hash_tools(step["meta"].get("tools", [])).encode())
    return h.hexdigest()


def cache_file(name: str) -> Path:
    return CACHE_DIR / f"{name}.hash"


def load_cache(name: str) -> str | None:
    f = cache_file(name)
    return f.read_text().strip() if f.exists() else None


def save_cache(name: str, value: str):
    cache_file(name).write_text(value)
