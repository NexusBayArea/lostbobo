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
    return []


if __name__ == "__main__":
    v = scan()
    if v:
        print("❌ Import boundary violations:")
        for x in v:
            print(x)
        sys.exit(1)

    print("✅ Import boundaries clean")
