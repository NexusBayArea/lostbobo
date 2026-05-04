from pathlib import Path


def run() -> bool:
    """API purity and architecture checks."""
    gate = Path("tools/check_api_purity.py")
    if not gate.exists():
        print("[API] SKIP (gate not found)")
        return True

    import subprocess

    result = subprocess.run(["python", str(gate)], capture_output=True, text=True)

    print(f"[API] stdout: {result.stdout.strip()}")
    print(f"[API] stderr: {result.stderr.strip()}")

    success = result.returncode == 0
    print("[API] API purity OK" if success else "[API] API violations detected")
    return success
