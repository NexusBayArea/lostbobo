#!/usr/bin/env python3
"""API module CI job."""

import subprocess
import sys


def main():
    print("Running API module tests...")
    result = subprocess.run(
        ["pytest", "tests/", "-v", "-k", "api"],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        sys.exit(1)
    print("API tests passed")


if __name__ == "__main__":
    main()
