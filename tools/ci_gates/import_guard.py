import ast
import os
import sys
from tools.runtime.contract import CONTRACT

VIOLATIONS = []


def scan_file(path: str):
    with open(path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=path)

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and not CONTRACT.is_allowed_import(node.module):
                VIOLATIONS.append((path, node.module))


def scan_repo(root="."):
    for base, dirs, files in os.walk(root):
        # skip virtual envs and hidden dirs
        if any(
            ignored in base
            for ignored in [".venv", ".git", "__pycache__", "node_modules"]
        ):
            continue

        for f in files:
            if f.endswith(".py"):
                scan_file(os.path.join(base, f))


if __name__ == "__main__":
    scan_repo()

    if VIOLATIONS:
        print("\nIMPORT BOUNDARY VIOLATIONS DETECTED:\n")
        for v in VIOLATIONS:
            print(f" - {v[0]} → {v[1]}")
        sys.exit(1)

    print("Import boundaries OK")
