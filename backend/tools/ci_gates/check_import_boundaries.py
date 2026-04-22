import sys
from pathlib import Path

# Project root is 'backend'
ROOT = Path("backend")

# Forbidden imports
RULES = {
    "app": ["worker"],
    "worker": ["app"],
}

EXEMPT_DIRS = {"runtime", "tools"}


def scan():
    violations = []

    for layer, forbidden in RULES.items():
        if layer in EXEMPT_DIRS:
            continue

        layer_path = ROOT / layer
        if not layer_path.exists():
            continue

        for py in layer_path.rglob("*.py"):
            text = py.read_text()

            for bad in forbidden:
                if f"import {bad}" in text or f"from {bad}" in text:
                    violations.append(f"{py}: illegal import of '{bad}'")

    return violations


if __name__ == "__main__":
    v = scan()
    if v:
        print("❌ Import boundary violations:")
        for x in v:
            print(x)
        sys.exit(1)

    print("✅ Import boundaries clean")
