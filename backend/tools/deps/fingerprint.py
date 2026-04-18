"""
Environment Fingerprint — Creates cryptographic identity for build environment

Generates SHA256 fingerprint of dependency artifacts to ensure CI == Docker == Worker parity.
"""

import hashlib
from pathlib import Path


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    files = [
        "requirements.lock.txt",
        "requirements.txt",
    ]

    combined = ""

    for f in files:
        if Path(f).exists():
            combined += hash_file(Path(f))

    fingerprint = hashlib.sha256(combined.encode()).hexdigest()

    Path("build.fingerprint").write_text(fingerprint + "\n")

    print("\nBUILD FINGERPRINT:")
    print(fingerprint)


if __name__ == "__main__":
    main()
