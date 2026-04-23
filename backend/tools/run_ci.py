#!/usr/bin/env python
"""
Single-command CI entrypoint for deterministic execution.

Usage:
    python tools/run_ci.py
"""
import os
import sys
import subprocess
from pathlib import Path

# path computed from cwd at runtime
BACKEND = Path.cwd()

sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(BACKEND))

# Stub required env vars for CI
os.environ.setdefault("RUNTIME_MODE", "ci")
os.environ.setdefault("SB_URL", "http://localhost:8080")
os.environ.setdefault("SB_TOKEN", "ci-stub-token")
os.environ.setdefault("SB_SECRET_KEY", "ci-stub-secret")
os.environ.setdefault("SB_JWT_SECRET", "ci-stub-jwt")
os.environ.setdefault("SB_PUB_KEY", "ci-stub-pubkey")
os.environ.setdefault("SB_DATA_URL", "http://localhost:8000")


def run(label: str, cmd: list[str], cwd=None) -> bool:
    print(f"[CI] Running: {label}")
    result = subprocess.run(cmd, cwd=cwd or BACKEND)
    if result.returncode != 0:
        print(f"[CI] FAILED: {label}")
        return False
    print(f"[CI] PASS: {label}")
    return True


def main():
    steps = [
        ("Ruff format check", ["python", "-m", "ruff", "format", "--check", "."]),
        ("Ruff lint", ["python", "-m", "ruff", "check", "."]),
        ("API purity check", ["python", "tools/check_api_purity.py"]),
        ("Import boundary check", ["python", "tools/ci_gates/check_import_boundaries.py"]),
    ]

    failed = []
    for label, cmd in steps:
        if not run(label, cmd, cwd=BACKEND):
            failed.append(label)

    if failed:
        print(f"\n[CI] {len(failed)} step(s) failed: {failed}")
        sys.exit(1)

    print("\n[CI] All checks passed")


if __name__ == "__main__":
    main()
