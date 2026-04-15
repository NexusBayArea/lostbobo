name: bootstrap.py

import subprocess
import sys


def run_step(name: str, cmd: list[str]) -> None:
    print(f"[Bootstrap] -> {name}")
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(f"[FAIL] {name}")
        sys.exit(result.returncode)

    print(f"[PASS] {name}")


def main(mode: str = "ci") -> None:
    """
    Ordered execution matters.
    Fail fast on first violation.
    """
    run_step(
        "System Contract",
        ["python", "tools/ci_gates/system_contract.py"],
    )

    # The existing steps will now be handled by system_contract.py
    # This bootstrap.py will become a wrapper for the system_contract.py
    # if mode == "ci":
    #    run("python -m pytest tests/ --tb=short -q")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
