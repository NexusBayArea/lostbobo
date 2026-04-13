"""
Policy Node — Gamma Stable (v11.0.0)

Enforces immutability rules against CI workflow files.
Fails the build if any mutable Docker tags (:latest, :stable) are found.

Usage:
    python ci/policy.py
"""
import sys
import pathlib


def check_mutable_tags() -> bool:
    """Scan all workflow YAML files for mutable tag usage. Returns True if clean."""
    violations: list[str] = []

    for path in pathlib.Path(".github/workflows").rglob("*.yml"):
        content = path.read_text()
        for line_no, line in enumerate(content.splitlines(), start=1):
            # Skip comment lines
            if line.strip().startswith("#"):
                continue
            if ":latest" in line or ":stable" in line:
                violations.append(f"  {path}:{line_no}: {line.strip()}")

    if violations:
        print("Policy violation — mutable Docker tags detected:")
        for v in violations:
            print(v)
        return False

    print("Policy: OK — no mutable tags found")
    return True


if __name__ == "__main__":
    if not check_mutable_tags():
        sys.exit(1)
