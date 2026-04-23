"""
Fingerprint Verification — Validates environment parity across builds

Ensures CI == Docker == Worker by verifying fingerprint matches.
"""

import subprocess
import sys
from pathlib import Path


def main() -> None:
    print("\n== ENVIRONMENT FINGERPRINT CHECK ==")

    if not Path("build.fingerprint").exists():
        print("WARNING: No build.fingerprint found, generating...")
        subprocess.run(["python", "backend/tools/deps/fingerprint.py"])

    expected = Path("build.fingerprint").read_text().strip()

    subprocess.run(["python", "backend/tools/deps/fingerprint.py"])

    actual = Path("build.fingerprint").read_text().strip()

    if expected != actual:
        print("FINGERPRINT MISMATCH")
        print("expected:", expected)
        print("actual:", actual)
        sys.exit(1)

    print("Fingerprint OK:", actual[:16] + "...")


if __name__ == "__main__":
    main()
