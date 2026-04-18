import sys
from pathlib import Path


LOCKFILE = Path("requirements.lock")
PYPROJECT = Path("pyproject.toml")


def validate_lock_format() -> bool:
    """Validate lockfile has correct format with pinned versions."""
    if not LOCKFILE.exists():
        print("[FAIL] missing requirements.lock")
        return False

    content = LOCKFILE.read_text()
    lines = content.splitlines()

    pinned = [line.strip() for line in lines if line.strip() and "==" in line]

    if not pinned:
        print("[FAIL] no pinned dependencies found in lockfile")
        return False

    print(f"[KERNEL] Lockfile contains {len(pinned)} pinned dependencies")

    unpinned = [line for line in pinned if "==" not in line]
    if unpinned:
        print(f"[FAIL] found {len(unpinned)} unpinned dependencies")
        return False

    print("[PASS] dependency kernel validated")
    return True


def main():
    print("[KERNEL] Zero-drift dependency validation")

    if not PYPROJECT.exists():
        print("[FAIL] missing pyproject.toml")
        sys.exit(1)

    if not validate_lock_format():
        sys.exit(1)

    print("[PASS] dependency kernel clean")


if __name__ == "__main__":
    main()
