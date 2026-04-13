"""CI runtime mode."""
import importlib
import logging
import subprocess
import sys

logger = logging.getLogger(__name__)


def run_ci_checks():
    """Run CI validation suite."""
    logger.info("[RUNTIME:CI] Starting CI checks")

    checks = [
        # FIX: __import__ returns the top-level package, not the submodule.
        # Use importlib.import_module for dotted paths.
        ("Import Test", _test_import),
        ("Boot Context Test", _test_boot_context),
        ("DAG Events Test", _test_dag_events),
    ]

    failed = []

    for check_name, check_func in checks:
        try:
            logger.info("[RUNTIME:CI] Running: %s...", check_name)
            check_func()
            logger.info("  PASS  %s", check_name)
        except Exception as e:
            logger.error("  FAIL  %s: %s", check_name, e)
            failed.append((check_name, e))

    # Optional: run pytest if available
    try:
        result = subprocess.run(
            ["pytest", "-xvs", "tests/"],
            # FIX: use text=True so stdout/stderr are str, not bytes
            # FIX: capture stderr too so the full failure output is visible
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            logger.info("  PASS  pytest suite")
        else:
            # stdout + stderr both available as str now
            combined = result.stdout + result.stderr
            logger.error("  FAIL  pytest:\n%s", combined)
            failed.append(("pytest", "Test failures"))
    except FileNotFoundError:
        logger.warning("  WARN  pytest not found, skipping")
    except subprocess.TimeoutExpired:
        logger.error("  FAIL  pytest timeout")
        failed.append(("pytest", "Timeout"))

    if failed:
        logger.error("[RUNTIME:CI] %d check(s) failed", len(failed))
        sys.exit(1)
    else:
        logger.info("[RUNTIME:CI] All checks passed")


# ---------------------------------------------------------------------------
# Individual check implementations
# ---------------------------------------------------------------------------

def _test_import():
    """Test that core config is importable and callable."""
    # FIX: importlib.import_module handles dotted paths correctly
    module = importlib.import_module("app.core.config")
    module.get_settings()


def _test_boot_context():
    """Test that boot context is accessible and fully populated."""
    from app.core.boot.context import boot_context
    assert boot_context.initialized, "Boot context not initialized"
    # NOTE: this assertion requires build_settings() to set boot_context.settings.
    # If it does not, remove this line or fix the stage.
    assert boot_context.settings is not None, "Settings not loaded"


def _test_dag_events():
    """Test DAG event system."""
    from app.core.dag.events import create_event
    event = create_event("test", {"data": "value"})
    assert event.type == "test"
    assert event.payload["data"] == "value"
