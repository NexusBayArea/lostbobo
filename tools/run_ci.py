#!/usr/bin/env python
"""
Single-command CI entrypoint for deterministic execution.

Usage:
    python tools/run_ci.py
    python tools/run_ci.py --replay trace.json
    python tools/run_ci.py --contract v2
"""
import os
import subprocess
import sys
import argparse


def run(name, cmd, check=True):
    print(f"\n[CI] {name}")
    result = subprocess.run(cmd, shell=True, cwd="backend")
    if check and result.returncode != 0:
        print(f"[FAIL] {name}")
        sys.exit(result.returncode)
    print(f"[PASS] {name}")
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="CI entrypoint")
    parser.add_argument("--replay", help="Replay trace file")
    parser.add_argument("--contract", help="Contract version to test")
    parser.add_argument("--seed", type=int, help="Random seed for deterministic runs")
    args = parser.parse_args()

    os.environ["RUNTIME_MODE"] = "ci"
    os.environ["SB_URL"] = os.environ.get("SB_URL", "http://localhost:8000")
    os.environ["SB_TOKEN"] = os.environ.get("SB_TOKEN", "ci-stub-token")
    os.environ["SB_SECRET_KEY"] = os.environ.get("SB_SECRET_KEY", "ci-stub-secret")
    os.environ["SB_JWT_SECRET"] = os.environ.get("SB_JWT_SECRET", "ci-stub-jwt")
    os.environ["SB_PUB_KEY"] = os.environ.get("SB_PUB_KEY", "ci-stub-pubkey")
    os.environ["SB_DATA_URL"] = os.environ.get("SB_DATA_URL", "http://localhost:8001")

    if args.seed:
        os.environ["SIMHPC_SEED"] = str(args.seed)

    run("Install runtime deps", "uv pip install -r requirements.api.lock")
    run("Install dev deps", "uv pip install -r requirements.dev.lock")

    run("Ruff lint", "ruff check . --config pyproject.toml")
    run("Ruff format check", "ruff format . --check --config pyproject.toml")

    run("Import check", "python -c 'from app.gateway import app; from worker.worker import worker; print(\"imports OK\")'")

    run("Tests", "pytest -q --tb=short ../tests/")

    if args.replay:
        run("Replay diff", f"python -m runtime.replay_diff {args.replay} {args.contract or 'v1'}", check=False)

    if args.contract:
        print(f"\n[CI] Contract version: {args.contract}")

    print("\n" + "=" * 50)
    print("CI PASSED")
    print("=" * 50)


if __name__ == "__main__":
    main()