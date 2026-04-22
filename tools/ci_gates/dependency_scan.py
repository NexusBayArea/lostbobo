"""
Dependency Scanner — Detects missing runtime dependencies before execution

Run as first bootstrap stage to fail fast on missing deps instead of at runtime.

Filters: stdlib, local modules, then enforces external dependencies.
"""

import ast
import sys
from pathlib import Path

ROOT = Path(".")

# Use system provided standard library names
STDLIB = set(sys.stdlib_module_names)

# Define internal root namespaces
INTERNAL_NAMESPACES = {"app", "worker", "packages", "tools", "ci", "docker", "docs", "frontend", "supabase", "tests", "compiler", "infra", "scripts"}


def get_local_modules() -> set:
    return INTERNAL_NAMESPACES


def extract_imports() -> set:
    deps = set()

    for file in ROOT.rglob("*.py"):
        path = str(file)
        if any(x in path for x in [".venv", ".git", "__pycache__", "node_modules"]):
            continue

        try:
            tree = ast.parse(file.read_text())
        except Exception:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    deps.add(n.name.split(".")[0])

            if isinstance(node, ast.ImportFrom) and node.module:
                deps.add(node.module.split(".")[0])

    return deps


def filter_external(deps: set, local_modules: set) -> list:
    external = []
    for d in deps:
        if d in STDLIB:
            continue
        if d in local_modules:
            continue
        external.append(d)
    return sorted(set(external))


def check_requirements() -> None:
    # Changed to enforce use of lockfile
    reqs_path = Path("requirements.api.lock")
    if not reqs_path.exists():
        print("ERROR: requirements.api.lock not found. Please run: uv pip compile pyproject.toml -o requirements.api.lock")
        sys.exit(1)

    reqs = reqs_path.read_text().lower()

    local_modules = get_local_modules()
    detected = extract_imports()
    external = filter_external(detected, local_modules)

    missing = []
    for dep in external:
        # Check against lockfile
        if dep not in reqs and dep.replace("_", "-") not in reqs:
            missing.append(dep)

    if missing:
        print("\nMISSING DEPENDENCIES DETECTED:")
        for m in missing:
            print(f" - {m}")
        print("\nAdd these to pyproject.toml and run: uv pip compile backend/pyproject.toml -o requirements.api.lock")
        sys.exit(1)

    print(f"Dependency scan OK: {len(external)} external packages verified in lockfile")


if __name__ == "__main__":
    check_requirements()
