#!/usr/bin/env python3
"""
Self-healing dependency resolver - installs missing dependencies before DAG execution

CRITICAL: This only runs BEFORE DAG execution, never during.
"""

import ast
import subprocess
import sys
from pathlib import Path

STANDARD_LIBRARY = {
    "sys",
    "os",
    "pathlib",
    "ast",
    "json",
    "subprocess",
    "typing",
    "dataclasses",
    "collections",
    "re",
    "time",
    "datetime",
    "uuid",
    "hashlib",
    "logging",
    "tempfile",
    "shutil",
    "contextlib",
    "operator",
    "functools",
    "itertools",
    "tools",
}

ALLOWED_AUTO_INSTALL = {
    "pyyaml",
    "pytest",
    "pytest-asyncio",
    "ruff",
}


def extract_imports(file_path: Path) -> set[str]:
    if not file_path.exists():
        return set()

    with open(file_path) as f:
        try:
            tree = ast.parse(f.read(), filename=str(file_path))
        except SyntaxError:
            return set()

    imports = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.add(n.name.split(".")[0])

        if isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])

    return imports


def install_package(pkg: str) -> None:
    print(f"[SELF-HEAL] Installing missing dependency: {pkg}")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", pkg],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def resolve(imports: set[str]) -> None:
    missing = []

    for mod in sorted(imports):
        if mod in STANDARD_LIBRARY:
            continue

        if mod in ALLOWED_AUTO_INSTALL:
            continue

        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)

    for mod in missing:
        if mod not in ALLOWED_AUTO_INSTALL:
            print(f"[SELF-HEAL] ERROR: Not in allowlist: {mod}")
            continue

        install_package(mod)

    if missing:
        print(f"[SELF-HEAL] Resolved {len(missing)} missing dependencies")
    else:
        print("[SELF-HEAL] All dependencies satisfied")


if __name__ == "__main__":
    files = [
        "backend/tools/bootstrap.py",
        "backend/tools/runtime/dag_executor.py",
        "backend/tools/ci_gates/system_contract.py",
    ]

    all_imports = set()
    for f in files:
        all_imports |= extract_imports(Path(f))

    resolve(all_imports)
