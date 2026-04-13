#!/usr/bin/env python3
"""Core module CI job."""

import subprocess
import sys


def main():
    print("Running core module tests...")
    result = subprocess.run(
        ["pytest", "tests/", "-v"],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        sys.exit(1)
    print("Core tests passed")


if __name__ == "__main__":
    main()
