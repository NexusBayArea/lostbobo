import sys
import ast
from pathlib import Path

ROOT = Path("backend")

RULES = {
    "app": {"forbidden": {"worker"}},
    "worker": {"forbidden": {"app"}},
}

EXEMPT_DIRS = {"runtime", "tools", "tests"}


def get_imports(file_path: Path):
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except Exception:
        return set()

    imports = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.add(n.name.split(".")[0])

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])

    return imports


def scan():
    violations = []

    for layer, rule in RULES.items():
        if layer in EXEMPT_DIRS:
            continue

        layer_path = ROOT / layer
        if not layer_path.exists():
            continue

        for py in layer_path.rglob("*.py"):
            imports = get_imports(py)

            for bad in rule["forbidden"]:
                if bad in imports:
                    violations.append(f"{py}: illegal import of '{bad}'")

    return violations


if __name__ == "__main__":
    v = scan()

    if v:
        print("❌ Import boundary violations:")
        for x in v:
            print(" -", x)
        sys.exit(1)

    print("✅ Import boundaries clean")
