from pathlib import Path


def run() -> bool:
    """Check unused dependencies."""
    gate = Path("tools/ci_gates/check_dependency_usage.py")
    if not gate.exists():
        print("[PRUNE] SKIP (gate not found)")
        return True

    import subprocess

    result = subprocess.run(["python", str(gate)], capture_output=True, text=True)

    success = result.returncode == 0
    print("[PRUNE] All dependencies are used" if success else "[PRUNE] Unused dependencies detected")
    return success
