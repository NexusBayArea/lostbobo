import subprocess
import sys


def ensure_deps():
    print("[KERNEL] Ensuring dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "ruff"], check=True)


def run():
    ensure_deps()

    stages = [
        "python -m ruff check . --select I --fix",
        "python -m ruff format .",
        "python -m ruff check . --select UP --fix",
        "python -m ruff check .",
    ]

    for cmd in stages:
        print(f"[KERNEL] {cmd}")
        result = subprocess.run(cmd, shell=True)

        if result.returncode != 0 and "check ." in cmd:
            print("[KERNEL] FAILED")
            return 1

    print("[KERNEL] SUCCESS")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
