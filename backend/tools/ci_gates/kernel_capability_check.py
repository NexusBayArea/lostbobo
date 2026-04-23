import sys
from pathlib import Path

from backend.tools.runtime.capabilities import CAPABILITIES


def main():
    errors = []

    for cap in CAPABILITIES.values():
        if not cap.enabled:
            continue

        for f in cap.required_files:
            if not Path(f).exists():
                errors.append(f"{cap.name}: missing {f}")

    if errors:
        print("[FAIL] kernel capability check:")
        for e in errors:
            print(" ", e)
        sys.exit(1)

    print("[PASS] kernel capability check")


if __name__ == "__main__":
    main()
