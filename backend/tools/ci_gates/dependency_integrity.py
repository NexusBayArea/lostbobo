#!/usr/bin/env python3
"""
Deterministic Dependency Integrity Check (CI-safe)

Enforces:
1. Lockfile exists and is readable
2. No forbidden packages in API lockfile
3. Dependency graph is internally consistent

No mutation. No caching. No state.
"""

import importlib.metadata as metadata
import sys
from pathlib import Path

LOCKFILE = Path(__file__).resolve().parents[1] / "requirements.api.lock"
FORBIDDEN = ["numpy", "scipy", "torch", "cuda"]


# ----------------------------
# 1. lockfile correctness
# ----------------------------


def check_lockfile():
    print("[deps] Checking lockfile exists...")

    if not LOCKFILE.exists():
        print(f"Lockfile not found: {LOCKFILE}")
        sys.exit(1)

    content = LOCKFILE.read_text()
    if len(content.strip()) == 0:
        print("Lockfile is empty")
        sys.exit(1)

    violations = [pkg for pkg in FORBIDDEN if f"\n{pkg}==" in content]
    if violations:
        print(f"API lockfile contaminated with forbidden packages: {violations}")
        sys.exit(1)

    print("[deps] Lockfile OK")


# ----------------------------
# 2. dependency graph validity
# ----------------------------


def check_dependency_graph():
    print("[deps] Checking dependency graph integrity...")

    installed = {dist.metadata["Name"].lower(): dist for dist in metadata.distributions()}
    errors = []

    for name, dist in installed.items():
        requires = dist.requires or []
        for req in requires:
            dep = req.split(";")[0].strip().split(" ")[0].lower()
            if dep and dep not in installed:
                errors.append(f"{name} → missing {dep}")

    if errors:
        print("Dependency graph invalid:")
        for e in errors:
            print(" -", e)
        sys.exit(1)

    print("[deps] Graph valid")


# ----------------------------
# main
# ----------------------------


def main():
    check_lockfile()
    print()

    check_dependency_graph()
    print()

    print("[deps] All checks passed")


if __name__ == "__main__":
    main()
