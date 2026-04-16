import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def bootstrap():
    import tools.runtime.deps  # hard fail if broken
    from tools.runtime.graph import GRAPH
    from tools.runtime.engine import ExecutionEngine
    from tools.runtime.nodes import register_default_nodes

    print("[BOOTSTRAP] V2 deterministic runtime starting")

    register_default_nodes()
    engine = ExecutionEngine()

    if not GRAPH.nodes:
        print("[BOOTSTRAP] empty graph — nothing to execute")
        return

    results = engine.run_all()

    print("[BOOTSTRAP] execution complete")
    print(results)


def main():
    bootstrap()


if __name__ == "__main__":
    main()
