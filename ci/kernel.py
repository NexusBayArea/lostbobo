"""
CI Kernel — Gamma Stable (v11.0.0)

Orchestrates module execution with a single bounded self-healing retry.
Safe by design: fixes are limited to ruff auto-format only.
No speculative edits, no LLM patching.

Usage:
    python ci/kernel.py --module api
    python ci/kernel.py --module worker
    python ci/kernel.py --module ci
"""
import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("kernel")

# Module → test target mapping
MODULE_TARGETS: dict[str, list[str]] = {
    "api": ["app/"],
    "worker": ["worker/"],
    "ci": ["ci/"],
}


def run_tests(targets: list[str]) -> int:
    """Run pytest against the given targets. Returns exit code."""
    cmd = ["python", "-m", "pytest", "--tb=short", "-q"] + targets
    log.info("Running: %s", " ".join(cmd))
    result = subprocess.run(cmd)
    return result.returncode


def attempt_safe_fix() -> None:
    """Apply bounded, safe auto-fix: ruff only. No code mutation."""
    log.info("Self-heal: running ruff --fix (safe, bounded)")
    subprocess.run(["python", "-m", "ruff", "check", ".", "--fix", "--silent"])


def main() -> None:
    if "--module" not in sys.argv:
        log.error("Missing --module argument")
        sys.exit(1)

    module = sys.argv[sys.argv.index("--module") + 1]

    if module == "noop":
        log.info("Module is noop — skipping execution")
        sys.exit(0)

    targets = MODULE_TARGETS.get(module)
    if not targets:
        log.error("Unknown module: %s", module)
        sys.exit(1)

    # Attempt 1
    rc = run_tests(targets)

    if rc != 0:
        log.warning("Tests failed (exit %d). Attempting safe auto-fix...", rc)
        attempt_safe_fix()
        # Attempt 2 (bounded — no further retries)
        rc = run_tests(targets)
        if rc != 0:
            log.error("Tests still failing after auto-fix. Marking module as failed.")

    sys.exit(rc)


if __name__ == "__main__":
    main()
