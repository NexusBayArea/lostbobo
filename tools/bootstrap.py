import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def bootstrap():
    import tools.runtime.deps  # ensures system integrity

    print("[BOOTSTRAP] loaded")

    from tools.runtime.graph import GRAPH
    from tools.runtime.engine import ExecutionEngine

    engine = ExecutionEngine()

    # TEMP: create minimal test node if graph empty
    if not GRAPH.nodes:
        print("[BOOTSTRAP] no graph registered yet")
        return

    # execute first node deterministically
    first = next(iter(GRAPH.nodes))
    result = engine.run(first)

    print("[BOOTSTRAP] execution result:", result)


def main():
    bootstrap()


if __name__ == "__main__":
    main()
