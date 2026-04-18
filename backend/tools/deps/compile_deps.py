"""
Dependency Compiler — Generates requirements files from code imports

Scans codebase, extracts imports, generates requirements.txt and requirements.lock.txt.
"""

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(".")

STDLIB = {
    "os",
    "sys",
    "math",
    "json",
    "time",
    "datetime",
    "pathlib",
    "typing",
    "collections",
    "itertools",
    "asyncio",
    "re",
    "subprocess",
    "contextlib",
    "enum",
    "uuid",
    "hashlib",
    "secrets",
    "random",
    "base64",
    "functools",
    "operator",
    "copy",
    "io",
    "abc",
    "warnings",
    "tempfile",
    "shutil",
    "glob",
    "fnmatch",
    "urllib",
    "email",
    "html",
    "xml",
    "csv",
    "logging",
    "traceback",
    "gc",
    "inspect",
    "dis",
    "pickle",
    "dbm",
    "sqlite3",
    "concurrent",
    "threading",
}


def extract_imports() -> set:
    deps = set()

    for file in ROOT.rglob("*.py"):
        path = str(file)
        if any(
            x in path for x in ["venv", ".git", ".venv", "__pycache__", "node_modules"]
        ):
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


def filter_deps(all_deps: set) -> list:
    return sorted([d for d in all_deps if d not in STDLIB])


def main() -> None:
    print("\n[DEPS] Scanning codebase for imports...")

    all_imports = extract_imports()
    runtime_deps = filter_deps(all_imports)

    print(f"[DEPS] Found {len(runtime_deps)} runtime dependencies")

    req_path = Path("requirements.txt")
    existing = req_path.read_text() if req_path.exists() else ""

    lines = []
    for dep in runtime_deps:
        dep_normalized = dep.replace("_", "-")
        for line in existing.splitlines():
            line_clean = line.strip().split("=")[0].replace("_", "-").lower()
            if line_clean == dep_normalized.lower():
                lines.append(line.strip())
                break
        else:
            lines.append(dep)

    req_path.write_text("\n".join(sorted(lines)) + "\n")
    print(f"[DEPS] Written requirements.txt ({len(lines)} packages)")

    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-r",
                "requirements.txt",
                "--dry-run",
            ],
            capture_output=True,
        )
    except Exception:
        pass

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True
        )
        if result.returncode == 0:
            locked = []
            for line in result.stdout.splitlines():
                if "==" in line and not line.startswith("#"):
                    locked.append(line.strip())
            locked.sort()
            Path("requirements.lock.txt").write_text("\n".join(locked) + "\n")
            print(f"[DEPS] Written requirements.lock.txt ({len(locked)} packages)")
    except Exception as e:
        print(f"[DEPS] Could not generate lock file: {e}")

    print("[DEPS] Done")


if __name__ == "__main__":
    main()
