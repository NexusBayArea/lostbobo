#!/usr/bin/env python
"""
Single-command CI entrypoint for deterministic execution.

Usage:
    python tools/run_ci.py
    python tools/run_ci.py --replay trace.json
    python tools/run_ci.py --contract v2
    python tools/run_ci.py --auto-fix  # Attempt auto-fix in sandbox
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND = REPO_ROOT / "backend"

sys.path.insert(0, str(REPO_ROOT))
os.chdir(BACKEND)


def run(name: str, cmd: str, check: bool = True) -> int:
    print(f"\n[CI] {name}")

    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        cwd=str(BACKEND),
    )

    if result.stdout:
        print(result.stdout)

    if check and result.returncode != 0:
        if result.stderr:
            print(result.stderr)

        full_log = (result.stdout or "") + "\n" + (result.stderr or "")

        from tools.ci.diagnose import diagnose, save_failure

        diagnosis = diagnose(full_log)

        print(diagnosis["suggested_command"])

        save_failure(diagnosis, "ci_failure.json")

        print(f"[FAIL] {name}")
        sys.exit(result.returncode)

    print(f"[PASS] {name}")
    return result.returncode


def run_with_auto_fix(name: str, cmd: str, auto_fix: bool = False) -> int:
    print(f"\n[CI] {name}")

    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        cwd=str(BACKEND),
    )

    if result.stdout:
        print(result.stdout)

    if result.returncode != 0:
        if result.stderr:
            print(result.stderr)

        full_log = (result.stdout or "") + "\n" + (result.stderr or "")

        from tools.ci.diagnose import diagnose, save_failure
        from tools.ci.fix_engine import sandbox_fix

        diagnosis = diagnose(full_log)
        print(diagnosis["suggested_command"])

        save_failure(diagnosis, "ci_failure.json")

        if auto_fix:
            print("\n[CI] Attempting auto-fix in sandbox...")

            fix_result = sandbox_fix(diagnosis, str(REPO_ROOT))

            if fix_result.get("applied"):
                print(f"[AUTO-FIX] Applied: {fix_result.get('fix_command')}")
                print(f"[AUTO-FIX] Changed files: {fix_result.get('changes', [])}")
                print("\n[AUTO-FIX SUCCESS]")
                print("Review changes and apply manually if needed.")
            else:
                print(f"[AUTO-FIX] Skipped: {fix_result.get('reason', 'not safe')}")

        print(f"[FAIL] {name}")
        sys.exit(result.returncode)

    print(f"[PASS] {name}")
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="CI entrypoint")
    parser.add_argument("--replay", help="Replay trace file")
    parser.add_argument("--contract", help="Contract version to test")
    parser.add_argument("--seed", type=int, help="Random seed for deterministic runs")
    parser.add_argument("--auto-fix", action="store_true", help="Attempt auto-fix in sandbox on failure")
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

    run("Install runtime deps", "uv venv && uv pip install --system -r requirements.api.lock")
    run("Install dev deps", "uv pip install --system -r requirements.dev.lock")
    run("Install pytest", "uv pip install --system pytest pytest-asyncio")
    run("Install package", "uv pip install --system -e .")

    run("Ruff lint", "ruff check . --config pyproject.toml")
    run("Ruff format check", "ruff format . --check --config pyproject.toml")

    run("Import check", "python3 -c 'from app.gateway import app; from worker.worker import worker; print(\"imports OK\")'")

    run("Runtime Isolation Gate", f"python3 {REPO_ROOT}/tools/ci_gates/runtime_isolation.py")

    run_func = lambda n, c: run_with_auto_fix(n, c, args.auto_fix) if args.auto_fix else run
    run_func("Tests", "python3 -m pytest -q --tb=short ../tests/")

    if args.replay:
        run("Replay diff", f"python -m runtime.replay_diff {args.replay} {args.contract or 'v1'}", check=False)

    if args.contract:
        print(f"\n[CI] Contract version: {args.contract}")

    print("\n" + "=" * 50)
    print("CI PASSED")
    print("=" * 50)


if __name__ == "__main__":
    main()