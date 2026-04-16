import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load_import(path: str):
    if path.startswith("side_effect:"):
        module = __import__(path.replace("side_effect:", ""), fromlist=["*"])
        return module

    if path.startswith("lazy:"):
        module = __import__(path.replace("lazy:", ""), fromlist=["*"])
        return module

    return __import__(path, fromlist=["*"])


def run():
    from tools.runtime.manifest import BOOT_MANIFEST
    from tools.runtime.lint_contract import LINT_CONTRACT

    print("[V3.1 BOOT] starting")

    raw_imports = []

    for step in BOOT_MANIFEST:
        raw_imports.extend(step.imports)

    violations = LINT_CONTRACT.validate_import_policy(raw_imports)

    if violations:
        raise RuntimeError(
            f"[LINT CONTRACT FAIL] invalid imports: {violations}"
        )

    for step in BOOT_MANIFEST:
        print(f"[BOOT] {step.name}")

        for imp in step.imports:
            load_import(imp)

        module_path, func_name = step.run.rsplit(".", 1)
        module = __import__(module_path, fromlist=["*"])
        getattr(module, func_name)()

    print("[V3.1 BOOT] complete")


if __name__ == "__main__":
    run()
