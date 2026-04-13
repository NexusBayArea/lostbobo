"""
DAG Compiler — Gamma Stable (v11.0.0)

Determines the minimal set of CI modules to execute based on changed files.
Outputs JSON to stdout for consumption by the workflow matrix.

Usage:
    python ci/dag_compiler.py > dag.json
"""
import json
import subprocess


def changed_files() -> list[str]:
    """Return files changed vs origin/main. Falls back to all files on error."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "origin/main"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        # First push / detached HEAD / no upstream — run everything
        return ["app/", "worker/", "ci/"]
    return result.stdout.splitlines()


# Map file prefix → CI module name
MODULE_MAP = {
    "app/": "api",
    "worker/": "worker",
    "ci/": "ci",
    "docker/": "ci",
    "pyproject.toml": "api",
}


def map_modules(files: list[str]) -> list[str]:
    modules: set[str] = set()
    for f in files:
        for prefix, module in MODULE_MAP.items():
            if f.startswith(prefix):
                modules.add(module)
    return sorted(modules)


if __name__ == "__main__":
    files = changed_files()
    modules = map_modules(files) or ["noop"]
    print(json.dumps({"modules": modules, "changed_files": files}))
