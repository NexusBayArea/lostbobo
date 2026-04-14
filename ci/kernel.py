"""
CI Kernel — Gamma Stable (v11.1.0)

Orchestrates module execution with a controlled learning layer.
Observes failures -> fingerprints -> predicts fixes -> applies -> learns.
"""

import subprocess
import sys
import logging

from ci.learning.predictor import predict
from ci.learning.executor import apply_fix
from ci.learning.failure_store import record
from ci.learning.fingerprint import fingerprint

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("kernel")

MODULE_TARGETS: dict[str, list[str]] = {
    "api": ["tests/"],
    "worker": ["tests/"],
    "ci": ["tests/"],
}


def run_with_learning(cmd):
    """Executes a command and applies learning-based self-healing if it fails."""
    log.info("Running: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        return 0

    err = result.stderr or result.stdout
    if not err:
        return result.returncode

    fp = fingerprint(err)
    log.warning("Command failed. Fingerprint: %s", fp)

    fix_cmd = predict(err)

    if fix_cmd:
        log.info("Predicted fix found: %s", fix_cmd)
        success = apply_fix(fix_cmd)
        record(fp, fix_cmd, success)

        if success:
            log.info("Fix applied successfully. Retrying original command...")
            retry = subprocess.run(cmd)
            return retry.returncode
        else:
            log.error("Predicted fix failed to apply.")
    else:
        log.warning("No predicted fix found in registry.")

    record(fp, None, False)
    return result.returncode


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

    cmd = ["python", "-m", "pytest", "--tb=short", "-q"] + targets

    rc = run_with_learning(cmd)

    if rc != 0:
        log.error("Tests still failing. Marking module as failed.")

    sys.exit(rc)


if __name__ == "__main__":
    if __package__ is None:
        raise RuntimeError(
            "Must run as module: python -m ci.kernel\n"
            "Do not run as: python ci/kernel.py"
        )
    main()
