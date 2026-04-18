import subprocess
import sys


def run(cmd: list[str]) -> int:
    print(f"\n[CI] $ {' '.join(cmd)}")
    return subprocess.call(cmd)


def fail(msg: str) -> None:
    print(f"\n[FAIL] {msg}")
    sys.exit(1)


def step(name: str, cmd: list[str]) -> None:
    rc = run(cmd)
    if rc != 0:
        fail(name)


def main():
    print("[CI-GATE] unified execution starting")

    step("format-check", ["python", "-m", "ruff", "format", ".", "--check"])

    step("lint", ["python", "-m", "ruff", "check", ".", "--exit-non-zero-on-fix"])

    step("import-graph", ["python", "-c", "import tools.runtime.kernel"])

    bootstrap_path = "tools/bootstrap.py"
    if subprocess.run(["python", bootstrap_path, "ci"]).returncode != 0:
        fail("contract")

    print("\n[CI-GATE] PASS (local == CI deterministic)")


if __name__ == "__main__":
    main()
