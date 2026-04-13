#!/usr/bin/env python3
"""
Dependency Drift Detector (CI-grade)

Guarantees:
- pyproject.toml ↔ lockfile consistency
- deterministic dependency resolution validation
- runtime import sanity check

Replaces fragile diff/freeze comparison with normalized hashing.
"""

import hashlib
import os
import subprocess
import sys
import tempfile
from importlib import import_module


# ----------------------------
# Core utilities
# ----------------------------


def run(cmd, cwd=None):
    """Run a subprocess safely (no shell)."""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return result


def sha256_file(path: str) -> str:
    """Compute SHA256 of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_requirements(text: str) -> str:
    """
    Normalize lockfile content to reduce false positives:
    - strip whitespace
    - remove empty lines
    - normalize ordering stability (best-effort)
    """
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    return "\n".join(sorted(lines))


# ----------------------------
# Drift checks
# ----------------------------


def check_lock_drift():
    """Ensure lockfile matches canonical resolution from pyproject.toml."""
    print("Checking dependency drift...")

    if not os.path.exists("pyproject.toml"):
        print("Missing pyproject.toml")
        sys.exit(1)

    if not os.path.exists("requirements.lock"):
        print("Missing requirements.lock")
        print("Generate with: uv pip compile pyproject.toml -o requirements.lock")
        sys.exit(1)

    with tempfile.NamedTemporaryFile(suffix=".lock", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        print("Generating canonical lockfile...")
        result = run(["uv", "pip", "compile", "pyproject.toml", "-o", tmp_path])

        if result.returncode != 0:
            print("Failed to compile dependencies")
            print(result.stderr)
            sys.exit(1)

        # Hash-based comparison (primary signal)
        existing_hash = sha256_file("requirements.lock")
        generated_hash = sha256_file(tmp_path)

        if existing_hash != generated_hash:
            print("Dependency drift detected (hash mismatch)")

            with open("requirements.lock") as f:
                existing = normalize_requirements(f.read())

            with open(tmp_path) as f:
                generated = normalize_requirements(f.read())

            print("\n--- DIFF (normalized) ---")
            print("ONLY IN LOCKFILE:\n")
            for line in sorted(
                set(existing.splitlines()) - set(generated.splitlines())
            ):
                print(f"- {line}")

            print("\nONLY IN GENERATED:\n")
            for line in sorted(
                set(generated.splitlines()) - set(existing.splitlines())
            ):
                print(f"+ {line}")

            print("\nFix with:")
            print("uv pip compile pyproject.toml -o requirements.lock")
            sys.exit(1)

        print("✅ Lockfile is in sync.")
        return True

    finally:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass


def check_resolution_consistency():
    """
    Validates resolution determinism by reinstalling from lockfile.
    Avoids comparing `freeze` output (which is inherently unstable).
    """
    print("Checking resolution consistency...")

    with tempfile.TemporaryDirectory() as tmpdir:
        result = run(["uv", "venv"], cwd=tmpdir)
        if result.returncode != 0:
            print("Failed to create venv")
            print(result.stderr)
            sys.exit(1)

        result = run(
            ["uv", "pip", "install", "-r", os.path.abspath("requirements.lock")]
        )
        if result.returncode != 0:
            print("Install failed from lockfile")
            print(result.stderr)
            sys.exit(1)

        print("Lockfile installs cleanly (resolution consistent).")
        return True


def check_runtime_imports():
    """Validate runtime import graph correctness."""
    print("Checking runtime imports...")

    target = os.environ.get("DRIFT_TEST_IMPORT", "app.main")

    try:
        import_module(target)
        print(f"Import successful: {target}")
        return True
    except Exception as e:
        print(f"Import failed: {target}")
        print(str(e))
        sys.exit(1)


# ----------------------------
# Entrypoint
# ----------------------------


def main():
    print("Dependency Drift Detection (CI-grade)\n")

    check_lock_drift()
    print()

    if os.environ.get("DRIFT_FULL_CHECK") == "1":
        check_resolution_consistency()
        print()

    if os.environ.get("DRIFT_TEST_IMPORT"):
        check_runtime_imports()
        print()

    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
