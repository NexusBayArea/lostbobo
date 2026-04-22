#!/usr/bin/env python
"""
Single-command CI entrypoint for deterministic execution.

Usage:
    python tools/run_ci.py
    python tools/run_ci.py --replay trace.json
    python tools/run_ci.py --auto-fix
"""
import os
import sys
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND = REPO_ROOT / "backend"

sys.path.insert(0, str(REPO_ROOT))
os.chdir(BACKEND)


def main():
    parser = argparse.ArgumentParser(description="CI entrypoint")
    parser.add_argument("--replay", help="Replay trace file")
    parser.add_argument("--auto-fix", action="store_true", help="Attempt auto-fix in sandbox on failure")
    args = parser.parse_args()

    os.environ["RUNTIME_MODE"] = "ci"
    os.environ["SB_URL"] = os.environ.get("SB_URL", "http://localhost:8080")
    os.environ["SB_TOKEN"] = os.environ.get("SB_TOKEN", "ci-stub-token")
    os.environ["SB_SECRET_KEY"] = os.environ.get("SB_SECRET_KEY", "ci-stub-secret")
    os.environ["SB_JWT_SECRET"] = os.environ.get("SB_JWT_SECRET", "ci-stub-jwt")
    os.environ["SB_PUB_KEY"] = os.environ.get("SB_PUB_KEY", "ci-stub-pubkey")
    os.environ["SB_DATA_URL"] = os.environ.get("SB_DATA_URL", "http://localhost:8000")

    from tools.ci.executor import run_dag

    run_dag(cwd=str(BACKEND))


if __name__ == "__main__":
    main()
