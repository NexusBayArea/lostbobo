import sys
from pathlib import Path
import subprocess

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def run_step(name: str, cmd: list[str]) -> None:
    print(f"[Bootstrap] -> {name}")

    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(f"[FAIL] {name}")
        sys.exit(result.returncode)

    print(f"[PASS] {name}")


def main():
    print("[Bootstrap] Contract stage (import test)")

    # real import validation
    import tools.runtime.contract  # noqa: F401

    run_step(
        "Kernel Boot",
        [sys.executable, "-m", "tools.runtime.kernel"],
    )


if __name__ == "__main__":
    main()
