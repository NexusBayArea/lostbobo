import subprocess
from pathlib import Path


def run() -> bool:
    """Run ruff format + lint checks."""
    root = Path(".")

    subprocess.run(["python", "-m", "ruff", "format", "."], cwd=root, capture_output=True)
    subprocess.run(["python", "-m", "ruff", "check", ".", "--fix"], cwd=root, capture_output=True)

    r1 = subprocess.run(["python", "-m", "ruff", "format", "--check", "."], cwd=root, capture_output=True, text=True)
    r2 = subprocess.run(["python", "-m", "ruff", "check", "."], cwd=root, capture_output=True, text=True)

    success = r1.returncode == 0 and r2.returncode == 0

    if success:
        print("[LINT] All files formatted and lint clean")
    else:
        print("[LINT] Issues found")
        if r1.stdout:
            print(r1.stdout)
        if r2.stdout:
            print(r2.stdout)

    return success
