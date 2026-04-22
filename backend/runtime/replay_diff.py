#!/usr/bin/env python
"""
CLI for replay + diff of execution traces.

Usage:
    python tools/runtime/replay_diff.py <trace_path> <contract_version> [executor_module]
    python tools/runtime/replay_diff.py trace_latest.json v1
"""
import sys
from pathlib import Path
from typing import Any, Callable, Dict

from runtime.diff import diff_nodes, format_diffs, save_diff_report
from runtime.replay import replay


def default_executor(node_name: str, input_data: dict) -> Any:
    """
    Default executor that loads and runs a node from the manifest.
    Replace this with custom executor for your system.
    """
    import importlib.util
    from runtime.manifest import load_manifest

    manifest = load_manifest()
    nodes = manifest.get("nodes", {})

    if node_name not in nodes:
        raise ValueError(f"Unknown node: {node_name}")

    node = nodes[node_name]
    path = node.get("path", "")

    if not path or not Path(path).exists():
        raise FileNotFoundError(f"Node path not found: {path}")

    spec = importlib.util.spec_from_file_location(node_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if hasattr(module, "run"):
        return module.run(**input_data)

    return {"status": "executed", "path": path}


def main():
    if len(sys.argv) < 3:
        print("Usage: python tools/runtime/replay_diff.py <trace_path> <contract_version> [executor_module]")
        sys.exit(1)

    trace_path = sys.argv[1]
    contract_version = sys.argv[2]
    executor_module = sys.argv[3] if len(sys.argv) > 3 else None

    if not Path(trace_path).exists():
        print(f"Error: Trace file not found: {trace_path}")
        sys.exit(1)

    executor: Callable[[str, dict], Any] = default_executor

    if executor_module:
        import importlib
        mod = importlib.import_module(executor_module)
        executor = getattr(mod, "executor", default_executor)

    print(f"Replaying trace: {trace_path}")
    print(f"Contract version: {contract_version}")

    try:
        replayed = replay(trace_path, contract_version, executor)
    except Exception as e:
        print(f"Error during replay: {e}")
        sys.exit(1)

    diffs = diff_nodes(replayed)

    if diffs:
        print("\n" + "=" * 60)
        print("DIFF DETECTED:")
        print("=" * 60)
        print(format_diffs(diffs))

        diff_report_path = "diff_report.json"
        save_diff_report(diffs, diff_report_path)
        print(f"\nDiff report saved to: {diff_report_path}")

        sys.exit(1)

    print("No differences detected.")
    sys.exit(0)


if __name__ == "__main__":
    main()