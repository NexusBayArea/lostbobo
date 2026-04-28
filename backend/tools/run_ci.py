#!/usr/bin/env python3
"""
Unified Deterministic CI runner with parallel execution and caching.

Usage:
    python tools/run_ci.py
"""
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from tools.ci.cache import hash_files, cache_key, is_cached, write_cache
from tools.ci.detect_changes import git_changed_files, classify

# When called with working-directory: backend in CI,
# cwd IS the backend directory already.
BACKEND = Path.cwd()


def step_inputs(label: str) -> list[Path]:
    base = Path(".")
    if "Lockfile" in label:
        return [base / "pyproject.toml"]
    if "Dependency pruning" in label:
        return list(base.rglob("app/**/*.py"))
    if "Ruff" in label:
        return list(base.rglob("**/*.py"))
    if "Import boundaries" in label:
        return list(base.rglob("**/*.py"))
    if "API purity" in label:
        return [base / "requirements.api.lock"]
    return []


def tool_version(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, text=True).strip()
    except Exception:
        return "unknown"


def run_step(label: str, cmd: list[str]) -> tuple[str, bool]:
    inputs = step_inputs(label)
    file_hash = hash_files(inputs)
    extra = tool_version(["python", "-m", "ruff", "--version"]) if "Ruff" in label else ""
    key = cache_key(label, file_hash, extra)

    if is_cached(key):
        print(f"[CI] SKIP (cached): {label}")
        return (label, True)

    print(f"[CI] Running: {label}")
    result = subprocess.run(cmd, cwd=BACKEND)

    if result.returncode != 0:
        print(f"[CI] FAILED: {label}")
        return (label, False)

    write_cache(key)
    print(f"[CI] PASS: {label}")
    return (label, True)


def run_parallel(steps: list[tuple[str, list[str]]], max_workers: int = 4):
    failed = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(run_step, label, cmd): label
            for label, cmd in steps
        }

        for future in as_completed(futures):
            label, ok = future.result()
            if not ok:
                failed.append(label)

    return failed


def main():
    files = git_changed_files()
    flags = classify(files)

    stage1 = []
    stage2 = []

    # --- Stage 1 (blocking) ---
    if flags["deps"]:
        stage1.append(("Lockfile sync", ["python", "tools/ci_gates/check_lock_sync.py"]))
        stage1.append(("Dependency pruning", ["python", "tools/ci_gates/check_dependency_usage.py"]))

    # --- Stage 2 (parallel) ---
    if flags["api"] or flags["runtime"] or flags["worker"]:
        stage2.append(("Ruff format check", ["python", "-m", "ruff", "format", "."]))
        stage2.append(("Ruff lint", ["python", "-m", "ruff", "check", ".", "--fix"]))

    stage2.append(("Import boundaries", ["python", "tools/ci_gates/check_import_boundaries.py"]))

    if flags["deps"]:
        stage2.append(("API purity check", ["python", "tools/check_api_purity.py"]))

    # --- fallback ---
    if flags["global"] or not files:
        print("[CI] Global change detected → full CI run")
        stage1 = [
            ("Lockfile sync", ["python", "tools/ci_gates/check_lock_sync.py"]),
            ("Dependency pruning", ["python", "tools/ci_gates/check_dependency_usage.py"]),
        ]
        stage2 = [
            ("Ruff format check", ["python", "-m", "ruff", "format", "."]),
            ("Ruff lint", ["python", "-m", "ruff", "check", ".", "--fix"]),
            ("API purity check", ["python", "tools/check_api_purity.py"]),
            ("Import boundaries", ["python", "tools/ci_gates/check_import_boundaries.py"]),
        ]

    # --- execute stage 1 (sequential, fail-fast) ---
    for label, cmd in stage1:
        _, ok = run_step(label, cmd)
        if not ok:
            print("\n[CI] Stopped at Stage 1 failure")
            sys.exit(1)

    # --- execute stage 2 (parallel) ---
    max_workers = int(os.environ.get("CI_MAX_WORKERS", "4"))
    failed = run_parallel(stage2, max_workers=max_workers)

    if failed:
        print(f"\n[CI] {len(failed)} parallel step(s) failed: {failed}")
        sys.exit(1)

    print("\n[CI] All checks passed")


if __name__ == "__main__":
    main()
