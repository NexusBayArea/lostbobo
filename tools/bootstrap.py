"""
System Bootstrap Gate — Single Source of Truth Enforcement

Collapses all CI enforcement into one deterministic gate:
- Structural integrity (import guard, dag compiler)
- Runtime contract validation
- Worker isolation safety
- Test execution

Usage:
    python tools/bootstrap.py ci      # full CI validation
    python tools/bootstrap.py worker  # worker-only validation
    python tools/bootstrap.py dev      # dev mode
"""

import subprocess
import sys


def run(cmd: str) -> None:
    print(f"\n[BOOTSTRAP] {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        raise SystemExit(f"BOOTSTRAP FAILED: {cmd}")


def main(mode: str = "ci") -> None:
    print(f"\n=== SYSTEM BOOTSTRAP START ({mode}) ===")

    # 1. Structural integrity (no code runs if this fails)
    run("python tools/ci_gates/import_guard.py")
    run("python tools/ci_gates/dag_compiler.py")

    # 2. Runtime contract validation
    run(f"python -m app.api.kernel --mode={mode} --dry-run")

    # 3. Worker isolation safety
    run("python tools/ci_gates/worker_isolation.py")

    # 4. Tests only after structure is validated
    if mode == "ci":
        run("python -m pytest tests/ --tb=short -q")

    print("\n=== SYSTEM BOOTSTRAP OK ===")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "ci"
    main(mode)
