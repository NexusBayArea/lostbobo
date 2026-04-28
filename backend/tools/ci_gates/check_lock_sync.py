#!/usr/bin/env python3
"""
Lockfile enforcement:
Ensures requirements.*.lock files are in sync with pyproject.toml.
"""

import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(cmd: list[str]) -> str:
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr)
        sys.exit(1)
    return result.stdout


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compile_lock(extra: str | None, output: Path):
    cmd = ["uv", "pip", "compile", "backend/pyproject.toml", "-o", str(output)]

    if extra:
        cmd.insert(3, "--extra")
        cmd.insert(4, extra)

    run(cmd)


def check(lock_name: str, extra: str | None):
    print(f"[LOCK] Checking {lock_name}")

    existing = ROOT / "backend" / lock_name

    if not existing.exists():
        print(f"[LOCK] Missing {lock_name}")
        sys.exit(1)

    with tempfile.NamedTemporaryFile(suffix=".lock", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        compile_lock(extra, tmp_path)

        if sha256(existing) != sha256(tmp_path):
            print(f"\n[LOCK] Drift detected in {lock_name}")
            print("Run:")
            if extra:
                print(f"  uv pip compile backend/pyproject.toml --extra {extra} -o backend/{lock_name}")
            else:
                print(f"  uv pip compile backend/pyproject.toml -o backend/{lock_name}")
            sys.exit(1)

        print(f"[LOCK] OK: {lock_name}")

    finally:
        tmp_path.unlink(missing_ok=True)


def main():
    check("requirements.api.lock", None)
    check("requirements.worker.lock", "worker")
    check("requirements.dev.lock", "dev")

    print("\n[LOCK] All lockfiles in sync")


if __name__ == "__main__":
    main()
