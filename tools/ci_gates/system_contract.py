"""
System Contract

Enforces integrity across:
- dependencies
- environment parity
- DAG validity
- runtime contract
- trace integrity (optional / evolving)
"""

import subprocess
import sys


def run_step(name: str, cmd: list[str]) -> None:
    print(f"
[System Contract] → {name}")
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(f"[FAIL] {name}")
        sys.exit(result.returncode)

    print(f"[PASS] {name}")


def main() -> None:
    """
    Ordered execution matters.
    Fail fast on first violation.
    """

    # 1. Dependency Integrity
    run_step(
        "Dependency Integrity",
        ["python", "tools/deps/verify_fingerprint.py"],
    )

    run_step(
        "Dependency Scan",
        ["python", "tools/deps/dependency_scan.py"],
    )

    # 2. Environment Parity (if separate)
    # (skip if already covered above)

    # 3. DAG Validity
    run_step(
        "DAG Validation",
        ["pytest", "-m", "dag"],
    )

    # 4. Runtime Contract
    run_step(
        "Runtime Contract",
        ["pytest", "-m", "runtime"],
    )

    # 5. Trace Validation (optional but HIGH SIGNAL)
    # Add when ready
    # run_step(
    #     "Trace Validation",
    #     ["pytest", "-m", "trace"],
    # )

    print("
[SYSTEM CONTRACT PASSED]")


if __name__ == "__main__":
    main()
