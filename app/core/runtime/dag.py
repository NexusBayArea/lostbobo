"""Unified DAG entrypoint for all runtime modes."""
import logging
import os

from app.core.boot.engine import run_boot_dag
from app.core.runtime.mode import RuntimeMode

logger = logging.getLogger(__name__)


def run_dag(mode: RuntimeMode = None):
    """
    Unified boot pipeline for ALL environments.

    Args:
        mode: Runtime mode. If None, reads from RUNTIME_MODE env var.

    Raises:
        ValueError: If RUNTIME_MODE env var holds an unrecognised value.
    """
    if mode is None:
        mode_str = os.getenv("RUNTIME_MODE", "dev")
        # FIX: wrap enum construction to emit a helpful error listing valid choices
        try:
            mode = RuntimeMode(mode_str)
        except ValueError:
            valid = [m.value for m in RuntimeMode]
            raise ValueError(
                f"Unrecognised RUNTIME_MODE '{mode_str}'. "
                f"Valid values: {valid}"
            ) from None

    logger.info("[DAG] Runtime mode: %s", mode.value)

    # Execute deterministic boot
    run_boot_dag()

    # FIX: lazy imports are intentional (avoids pulling heavy deps for unused modes).
    # A missing dependency in one branch won't affect other modes at startup.
    # Run with RUNTIME_MODE=<mode> python -c "import app" to validate imports early.
    if mode == RuntimeMode.API:
        from app.core.runtime.api import start_api
        start_api()

    elif mode == RuntimeMode.WORKER:
        from app.core.runtime.worker import start_worker
        start_worker()

    elif mode == RuntimeMode.CI:
        from app.core.runtime.ci import run_ci_checks
        run_ci_checks()

    elif mode == RuntimeMode.DEV:
        from app.core.runtime.dev import start_dev
        start_dev()
