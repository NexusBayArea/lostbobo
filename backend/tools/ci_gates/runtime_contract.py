from pathlib import Path
import sys


def run_runtime_contract():
    if not Path("requirements.txt").exists():
        print("Missing requirements.txt (runtime contract not defined)")
        sys.exit(1)

    print("Runtime contract (requirements.txt) validated.")


if __name__ == "__main__":
    run_runtime_contract()
