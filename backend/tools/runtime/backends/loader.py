import os
import tarfile
from pathlib import Path

ASSET_DIR = Path(".simhpc/runtime")

def ensure_asset(name, archive_path):
    target = ASSET_DIR / name

    if target.exists():
        return target

    target.mkdir(parents=True, exist_ok=True)

    with tarfile.open(archive_path, "r:gz") as tar:
        tar.extractall(path=target)

    return target

def set_runtime_env(lib_path: Path):
    """Sets LD_LIBRARY_PATH to ensure dynamic libraries are found."""
    current_ld = os.environ.get("LD_LIBRARY_PATH", "")
    new_ld = f"{lib_path}:{current_ld}"
    os.environ["LD_LIBRARY_PATH"] = new_ld
    return new_ld
