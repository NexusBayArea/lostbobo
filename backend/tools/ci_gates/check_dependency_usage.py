#!/usr/bin/env python3
"""
Dependency pruning check:
Fail CI if declared dependencies are not used in code.
"""

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # Project Root
BACKEND = ROOT / "backend"


# --- config --------------------------------------------------

SRC_DIRS = [
    BACKEND / "app",
    BACKEND / "runtime",
    BACKEND / "worker",
]

# packages that are allowed to be "unused" (infra / optional)
ALLOWLIST = {
    "uvicorn",  # entrypoint only
    "pytest",  # test-only
    "ruff",  # dev-only
    "mypy",  # dev-only
    "pillow",  # dependency of qrcode
    "setuptools",  # build-only
    "structlog",  # core logging
    "tenacity",  # core retries
    "python_dotenv",  # core env loading
}

# mapping from pyproject name (normalized) to import name
IMPORT_MAP = {
    "python_dotenv": "dotenv",
}


# --- helpers -------------------------------------------------


def get_declared_dependencies():
    pyproject = ROOT / "pyproject.toml"

    if not pyproject.exists():
        print(f"[DEPS] pyproject.toml not found at {pyproject.resolve()}")
        return set()

    text = pyproject.read_text()

    deps = set()

    in_deps = False
    for line in text.splitlines():
        line = line.strip()

        if line.startswith("[project]"):
            continue

        if line.startswith("dependencies"):
            in_deps = True
            continue

        if in_deps:
            if line.startswith("]"):
                break
            if line.startswith('"'):
                # Extract package name: "pkg>=1.0" -> "pkg"
                pkg_match = re.search(r'"([^">=<!~]+)', line)
                if pkg_match:
                    pkg = pkg_match.group(1).split("[")[0]
                    deps.add(pkg.lower().replace("-", "_"))

    return deps


def extract_imports():
    imports = set()

    for base in SRC_DIRS:
        if not base.exists():
            continue

        for py in base.rglob("*.py"):
            try:
                tree = ast.parse(py.read_text(encoding="utf-8"))
            except Exception:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for n in node.names:
                        imports.add(n.name.split(".")[0].lower())

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split(".")[0].lower())

    return imports


# --- main ----------------------------------------------------


def main():
    declared = get_declared_dependencies()
    used = extract_imports()

    unused = []

    for dep in declared:
        import_name = IMPORT_MAP.get(dep, dep)
        if import_name not in used and dep not in ALLOWLIST:
            unused.append(dep)

    if unused:
        print("\n[PRUNE] Unused dependencies detected:")
        for d in sorted(unused):
            print(f"  - {d}")
        print("\nRemove them from pyproject.toml if truly unused.")
        sys.exit(1)

    print("[PRUNE] All dependencies are used")
    return 0


if __name__ == "__main__":
    sys.exit(main())
