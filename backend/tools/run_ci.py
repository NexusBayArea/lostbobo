#!/usr/bin/env python
"""
Single-command CI entrypoint for deterministic execution.
Run from backend/ directory: python tools/run_ci.py
"""

import os
import subprocess
import sys
from pathlib import Path

# When called with working-directory: backend in CI,
# cwd IS the backend directory already.
BACKEND = Path.cwd()

os.environ.setdefault("RUNTIME_MODE", "ci")
os.environ.setdefault("SB_URL", "http://localhost:8080")
os.environ.setdefault("SB_TOKEN", "ci-stub-token")
os.environ.setdefault("SB_SECRET_KEY", "ci-stub-secret")
os.environ.setdefault("SB_JWT_SECRET", "ci-stub-jwt")
os.environ.setdefault("SB_PUB_KEY", "ci-stub-pubkey")
os.environ.setdefault("SB_DATA_URL", "http://localhost:8000")


def run(label: str, cmd: list[str]) -> bool:
    print(f"[CI] Running: {label}")
    result = subprocess.run(cmd, cwd=BACKEND)
    if result.returncode != 0:
        print(f"[CI] FAILED: {label}")
        return False
    print(f"[CI] PASS: {label}")
    return True


def main():
    steps = [
        ("Ruff format check", ["python", "-m", "ruff", "format", "--check", "."]),
        ("Ruff lint",         ["python", "-m", "ruff", "check", ".", "--config", "pyproject.toml"]),
("Ruff format check", ["python", "-m", "ruff", "format", "--check", ".", "--config", "pyproject.toml"]),
        ("API purity check", ["python", "backend/tools/check_api_purity.py"]),
        ("Import boundaries", ["python", "backend/tools/ci_gates/check_import_boundaries.py"]),
    ]

    failed = []
    for label, cmd in steps:
        if not run(label, cmd):
            failed.append(label)

    if failed:
        print(f"\n[CI] {len(failed)} step(s) failed: {failed}")
        sys.exit(1)

    print("\n[CI] All checks passed")


if __name__ == "__main__":
    main()
