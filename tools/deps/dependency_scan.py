"""
Dependency Scan — Validates package dependencies are correct
"""

import subprocess
import sys
from pathlib import Path


def main() -> None:
    print("\n== DEPENDENCY SCAN ==")

    if not Path("pyproject.toml").exists():
        print("ERROR: pyproject.toml not found")
        sys.exit(1)

    print("pyproject.toml found")

    result = subprocess.run(
        ["pip", "install", "--dry-run", "-e", ".[dev]"], capture_output=True
    )

    if result.returncode != 0:
        print("ERROR: Dependency installation failed")
        print(result.stderr.decode())
        sys.exit(1)

    print("Dependencies OK")


if __name__ == "__main__":
    main()
