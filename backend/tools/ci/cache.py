import hashlib
import json
from pathlib import Path

CACHE_DIR = Path(".ci_cache")
CACHE_DIR.mkdir(exist_ok=True)


def hash_files(paths: list[Path]) -> str:
    h = hashlib.sha256()

    for p in sorted(paths):
        if p.exists():
            h.update(p.read_bytes())

    return h.hexdigest()


def cache_key(name: str, file_hash: str, extra: str = "") -> str:
    base = f"{name}:{file_hash}:{extra}"
    return hashlib.sha256(base.encode()).hexdigest()


def cache_path(key: str) -> Path:
    return CACHE_DIR / key


def is_cached(key: str) -> bool:
    return cache_path(key).exists()


def write_cache(key: str):
    cache_path(key).write_text("ok")


def clear_cache():
    for f in CACHE_DIR.glob("*"):
        f.unlink()
