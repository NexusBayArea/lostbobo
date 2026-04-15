import subprocess
import sys
import tempfile
from pathlib import Path


def run_step(name: str, cmd: list[str]) -> None:
    print(f"[Bootstrap] -> {name}")
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(f"[FAIL] {name}")
        sys.exit(result.returncode)

    print(f"[PASS] {name}")


def validate_dependency_lock():
    print("[BOOTSTRAP] Dependency lock validation")

    if not Path("pyproject.toml").exists():
        print("[FAIL] pyproject.toml not found")
        sys.exit(1)

    if not Path("requirements.lock").exists():
        print("[FAIL] requirements.lock not found")
        print("Generate with: uv pip compile pyproject.toml -o requirements.lock")
        sys.exit(1)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".lock", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            ["uv", "pip", "compile", "pyproject.toml", "-o", tmp_path],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"[FAIL] Dependency compilation failed: {result.stderr}")
            sys.exit(1)

        with open("requirements.lock") as f:
            existing = f.read()
        with open(tmp_path) as f:
            generated = f.read()

        with open("requirements.lock") as f:
            existing = f.read()
        with open(tmp_path) as f:
            generated = f.read()

        existing_lines = [
            line
            for line in existing.strip().split("\n")
            if line and not line.startswith("#")
        ]
        generated_lines = [
            line
            for line in generated.strip().split("\n")
            if line and not line.startswith("#")
        ]

        if set(existing_lines) != set(generated_lines):
            print("[FAIL] Dependency drift detected!")
            print("Run: uv pip compile pyproject.toml -o requirements.lock")
            sys.exit(1)

        print("[PASS] Dependency lock validated")

    finally:
        if Path(tmp_path).exists():
            Path(tmp_path).unlink()


def dependency_healing_phase():
    print("[BOOTSTRAP] Dependency Healing Phase")

    project_files = [
        "tools/bootstrap.py",
        "tools/runtime/dag_executor.py",
        "tools/ci_gates/system_contract.py",
    ]

    result = subprocess.run(
        ["python", "tools/deps/self_heal_deps.py"],
        input="\n".join(project_files),
        text=True,
    )

    if result.returncode != 0:
        print("[FAIL] Dependency Healing")
        sys.exit(result.returncode)

    print("[PASS] Dependency Healing")


def main(mode: str = "ci") -> None:
    validate_dependency_lock()

    dependency_healing_phase()

    run_step(
        "DAG Executor",
        ["python", "tools/runtime/dag_executor.py"],
    )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
