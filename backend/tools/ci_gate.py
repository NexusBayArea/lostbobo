import subprocess
import sys


def run_cmd(cmd):
    print(f"[CI] $ {' '.join(cmd)}")
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print(f"[FAIL] {cmd[2] if len(cmd) > 2 else cmd[0]}")
        sys.exit(res.returncode)


def main():
    print("[CI-GATE] Unified execution starting")

    # 1. Linting
    run_cmd(["python3", "-m", "ruff", "check", "backend/", "--fix"])
    run_cmd(["python3", "-m", "ruff", "format", "backend/", "--check"])

    # 2. Call your System Contract
    run_cmd(["python3", "backend/tools/ci_gates/system_contract.py"])


if __name__ == "__main__":
    main()
