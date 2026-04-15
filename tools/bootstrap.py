import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.runtime.contract import CONTRACT
import subprocess


def run_step(name: str, cmd: list[str]) -> None:
    print(f"[Bootstrap] -> {name}")
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(f"[FAIL] {name}")
        sys.exit(result.returncode)

    print(f"[PASS] {name}")


def main(mode: str = "ci") -> None:
    # validate contract first
    print("[Bootstrap] Contract validation OK")
    
    run_step(
        "Kernel Boot",
        [sys.executable, "-m", "tools.runtime.kernel"],
    )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
