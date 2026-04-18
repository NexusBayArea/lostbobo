#!/usr/bin/env python3
"""
DAG Validator - enforces contract manifest integrity

This validates that all required nodes exist and are properly declared
before any CI execution can run.
"""

import yaml
import sys
from pathlib import Path


def load_manifest():
    manifest_path = Path("tools/ci_manifest.yml")
    if not manifest_path.exists():
        print("[DAG VALIDATION FAILED] - manifest not found")
        sys.exit(1)

    with open(manifest_path, "r") as f:
        return yaml.safe_load(f)


def validate():
    manifest = load_manifest()
    missing = []
    errors = []

    for name, node in manifest.get("nodes", {}).items():
        path = node.get("path")
        if not path:
            errors.append(f"Node '{name}' missing 'path' field")
            continue

        path_obj = Path(path)
        if not path_obj.exists():
            missing.append((name, path))

    if errors:
        print("\n[DAG VALIDATION FAILED]")
        for err in errors:
            print(f" - {err}")
        sys.exit(1)

    if missing:
        print("\n[DAG VALIDATION FAILED]")
        print("Missing required nodes:")
        for name, path in missing:
            print(f" - {name}: {path}")
        sys.exit(1)

    print("[DAG VALIDATION PASSED]")
    print(f"Validated {len(manifest.get('nodes', {}))} nodes")


if __name__ == "__main__":
    validate()
