#!/usr/bin/env python3
"""
Unified Deterministic CI runner.

Usage:
    python tools/run_ci.py
"""

import subprocess
import sys
from pathlib import Path
from tools.ci.detect_changes import git_changed_files, classify

# When called with working-directory: backend in CI,
# cwd IS the backend directory already.
BACKEND = Path.cwd()


def run(label: str, cmd: list[str]) -> bool:
    print(f"[CI] Running: {label}")
    result = subprocess.run(cmd, cwd=BACKEND)
    if result.returncode != 0:
        print(f"[CI] FAILED: {label}")
        return False
    print(f"[CI] PASS: {label}")
    return True


def main():
    files = git_changed_files()
    flags = classify(files)

    steps = []

    # --- always safe minimal checks ---
    steps.append(("Import boundaries", ["python", "tools/ci_gates/check_import_boundaries.py"]))

    # --- dependency-related ---
    if flags["deps"]:
        steps.insert(0, ("Lockfile sync", ["python", "tools/ci_gates/check_lock_sync.py"]))
        steps.append(("Dependency pruning", ["python", "tools/ci_gates/check_dependency_usage.py"]))
        steps.append(("API purity check", ["python", "tools/check_api_purity.py"]))

    # --- code-related ---
    if flags["api"] or flags["runtime"] or flags["worker"]:
        steps.append(("Ruff format check", ["python", "-m", "ruff", "format", "."]))
        steps.append(("Ruff lint", ["python", "-m", "ruff", "check", ".", "--fix"]))

    # --- tooling changes ---
    if flags["tools"]:
        steps.append(("Ruff lint (tools)", ["python", "-m", "ruff", "check", "tools"]))

    # --- fallback ---
    if flags["global"] or not files:
        print("[CI] Global change detected → full CI run")
        steps = [
            ("Lockfile sync", ["python", "tools/ci_gates/check_lock_sync.py"]),
            ("Dependency pruning", ["python", "tools/ci_gates/check_dependency_usage.py"]),
            ("Ruff format check", ["python", "-m", "ruff", "format", "."]),
            ("Ruff lint", ["python", "-m", "ruff", "check", ".", "--fix"]),
            ("API purity check", ["python", "tools/check_api_purity.py"]),
            ("Import boundaries", ["python", "tools/ci_gates/check_import_boundaries.py"]),
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
