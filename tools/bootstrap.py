import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.runtime.manifest import BOOT_MANIFEST


def load_import(path: str):
    module = __import__(path, fromlist=["*"])
    return module


def run():
    print("[V3 BOOT] starting deterministic manifest execution")

    context = {}

    for step in BOOT_MANIFEST:
        print(f"[V3 BOOT] step: {step.name}")

        for imp in step.imports:
            context[imp] = load_import(imp)

        # execute run target
        module_path, func_name = step.run.rsplit(".", 1)
        module = load_import(module_path)
        getattr(module, func_name)()

    print("[V3 BOOT] complete")


if __name__ == "__main__":
    run()
