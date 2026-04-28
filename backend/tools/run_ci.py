#!/usr/bin/env python3
"""
Unified Deterministic CI runner with parallel stage execution.

Usage:
    python tools/run_ci.py
"""
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from tools.ci.detect_changes import git_changed_files, classify

# When called with working-directory: backend in CI,
# cwd IS the backend directory already.
BACKEND = Path.cwd()


def run_step(label: str, cmd: list[str]) -> tuple[str, bool]:
    print(f"[CI] Running: {label}")
    result = subprocess.run(cmd, cwd=BACKEND)
    if result.returncode != 0:
        print(f"[CI] FAILED: {label}")
        return (label, False)
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
