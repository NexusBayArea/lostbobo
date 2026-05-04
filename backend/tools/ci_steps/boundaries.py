from pathlib import Path


def run() -> bool:
    """Enforce import boundaries."""
    gate = Path("tools/ci_gates/check_import_boundaries.py")
    if not gate.exists():
        print("[BOUNDARIES] SKIP (gate not found)")
        return True

    import subprocess

    result = subprocess.run(["python", str(gate)], capture_output=True, text=True)

    success = result.returncode == 0
    print("[BOUNDARIES] Import boundaries clean" if success else "[BOUNDARIES] Boundary violation")
    return success
