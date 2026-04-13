#!/usr/bin/env python3
"""Hash computation for module cache."""

import hashlib
import json
import subprocess
import sys


def get_module_files(module: str) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", f"app/{module}", f"ci/jobs/{module}.sh"],
        capture_output=True,
        text=True,
    )
    return [f for f in result.stdout.splitlines() if f]


def hash_file(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except FileNotFoundError:
        return ""


def hash_module(module: str, dep_hashes: dict) -> str:
    files = get_module_files(module)
    h = hashlib.sha256()

    for f in sorted(files):
        content = hash_file(f)
        if content:
            h.update(content.encode())

    for dep in sorted(dep_hashes.get(module, [])):
        h.update(dep.encode())

    return h.hexdigest()[:16]


def main():
    module = sys.argv[1] if len(sys.argv) > 1 else "core"

    deps = {}
    try:
        with open("ci/cache_state.json") as f:
            deps = json.load(f)
    except FileNotFoundError:
        pass

    result = hash_module(module, deps)
    print(result)


if __name__ == "__main__":
    main()
