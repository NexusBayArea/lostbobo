from pathlib import Path


def run() -> bool:
    """Check lockfile synchronization."""
    gate = Path("tools/ci_gates/check_lock_sync.py")
    if not gate.exists():
        print("[LOCK] SKIP (gate not found)")
        return True

    import subprocess

    result = subprocess.run(["python", str(gate)], capture_output=True, text=True)

    if result.returncode == 0:
        print("[LOCK] Lockfiles in sync")
        return True
    else:
        print("[LOCK] Lockfile check failed")
        return False
