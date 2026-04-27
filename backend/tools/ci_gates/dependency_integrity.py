#!/usr/bin/env python3
"""
Deterministic Dependency Integrity Check (CI-safe)

Enforces:
1. Lockfile is canonical (uv compile match)
2. Dependency graph is internally consistent
3. No missing / broken requirements

No mutation. No caching. No state.
"""

import hashlib
import subprocess
import sys
import tempfile
import importlib.metadata as metadata


# ----------------------------
# utils
# ----------------------------


def run(cmd):
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )


# ----------------------------
# 1. lockfile correctness
# ----------------------------


def check_lockfile():
    print("[deps] Checking lockfile determinism...")

    with tempfile.NamedTemporaryFile(suffix=".lock", delete=False) as tmp:
        tmp_path = tmp.name

    result = run(["uv", "pip", "compile", "pyproject.toml", "-o", tmp_path])

    if result.returncode != 0:
        print(result.stderr)
        sys.exit(1)

    with open("requirements.lock") as f:
        committed = f.read()

    with open(tmp_path) as f:
        generated = f.read()

    if hashlib.sha256(committed.encode()).hexdigest() != hashlib.sha256(generated.encode()).hexdigest():
        print("Lockfile drift detected")
        sys.exit(1)

    print("[deps] Lockfile OK")


# ----------------------------
# 2. dependency graph validity
# ----------------------------


def check_dependency_graph():
    print("[deps] Checking dependency graph integrity...")

    installed = {dist.metadata["Name"]: dist for dist in metadata.distributions()}

    errors = []

    for name, dist in installed.items():
        requires = dist.requires or []

        for req in requires:
            dep = req.split(";")[0].strip().split(" ")[0]

            if dep and dep not in installed:
                errors.append(f"{name} → missing {dep}")

    if errors:
        print("Dependency graph invalid:")
        for e in errors:
            print(" -", e)
        sys.exit(1)

    print("[deps] Graph valid")


# ----------------------------
# 3. optional import sanity
# ----------------------------


def check_import():
    target = "app.main"

    print(f"[deps] Import check: {target}")

    try:
        __import__(target)
    except Exception as e:
        print("Import failed:", e)
        sys.exit(1)

    print("[deps] Import OK")


# ----------------------------
# main
# ----------------------------


def main():
    check_lockfile()
    print()

    check_dependency_graph()
    print()

    # optional but recommended
    check_import()
    print()

    print("[deps] All checks passed")


if __name__ == "__main__":
    main()
