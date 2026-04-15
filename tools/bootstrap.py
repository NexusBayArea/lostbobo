import subprocess
import sys
import json
from pathlib import Path


def run_step(name: str, cmd: list[str]) -> None:
    print(f"[Bootstrap] -> {name}")
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(f"[FAIL] {name}")
        sys.exit(result.returncode)

    print(f"[PASS] {name}")


def validate_dependency_kernel():
    print("[KERNEL] Hermetic dependency validation")

    result = subprocess.run(
        ["python", "tools/deps/hermetic_lock.py"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("[FAIL] dependency kernel drift")
        print(result.stderr)
        sys.exit(1)

    print("[PASS] dependency kernel stable")


def dependency_healing_phase():
    print("[BOOTSTRAP] Dependency Healing Phase")

    project_files = [
        "tools/bootstrap.py",
        "tools/ci_gates/dag_compiler.py",
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


def validate_dag_contract():
    print("[KERNEL] DAG contract validation")

    manifest = Path("tools/ci_manifest.yml")
    compiler = Path("tools/ci_gates/dag_compiler.py")

    if not manifest.exists():
        print("[FAIL] missing tools/ci_manifest.yml")
        sys.exit(1)

    if not compiler.exists():
        print("[FAIL] missing dag_compiler.py")
        sys.exit(1)

    result = subprocess.run(
        ["python", str(compiler)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("[FAIL] DAG compilation failed")
        print(result.stderr)
        sys.exit(1)

    try:
        output = json.loads(result.stdout)
        if "modules" not in output:
            print("[FAIL] DAG output missing 'modules' key")
            sys.exit(1)
        if not isinstance(output.get("modules"), list):
            print("[FAIL] DAG output 'modules' must be a list")
            sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"[FAIL] DAG output invalid JSON: {e}")
        sys.exit(1)

    print("[PASS] DAG contract valid")


def main(mode: str = "ci") -> None:
    validate_dependency_kernel()

    dependency_healing_phase()

    validate_dag_contract()

    run_step(
        "DAG Compile (source of truth)",
        ["python", "tools/ci_gates/dag_compiler.py"],
    )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
