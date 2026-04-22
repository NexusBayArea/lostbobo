import subprocess
import sys
import re


def ensure_deps():
    print("[KERNEL] Ensuring dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "ruff"], check=True)


def count_violations():
    """Counts current Ruff violations to prevent non-convergence."""
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "."],
        capture_output=True,
        text=True,
    )
    # Ruff outputs: "Found 25 errors."
    match = re.search(r"Found (\d+) error", result.stdout)
    if match:
        return int(match.group(1))
    return 0


def run_stage(cmd, name):
    before = count_violations()
    print(f"[KERNEL] {name}: Running {cmd}")
    
    result = subprocess.run(cmd, shell=True)
    
    after = count_violations()
    print(f"[KERNEL] {name}: {before} -> {after} violations")
    
    if after > before:
        print(f"[KERNEL] {name}: FAILED - State regression detected!")
        return False
    return True


def run():
    ensure_deps()

    stages = [
        ("python -m ruff check . --select I --fix", "Import Fix"),
        ("python -m ruff format .", "Format"),
        ("python -m ruff check . --select UP --fix", "Typing Fix"),
        ("python -m ruff check . --fix --unsafe-fixes", "Unsafe Fix Completion"),
    ]

    for cmd, name in stages:
        if not run_stage(cmd, name):
            return 1

    # Final validation pass
    print("[KERNEL] Final Validation...")
    if count_violations() == 0:
        print("[KERNEL] SUCCESS - System converged")
        return 0
    else:
        print("[KERNEL] FAILED - Strict validation failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(run())
