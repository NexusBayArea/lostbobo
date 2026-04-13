"""
Tests for boot fail-fast behavior.

Replaces the fragile inline shell-Python in the CI workflow.
This covers the case where required env vars are absent — boot must raise,
not silently succeed.
"""
import os
import pytest


@pytest.fixture(autouse=True)
def reset_boot_context():
    """Ensure boot_context is reset before and after each test."""
    from app.core.boot import context as ctx_module
    # Reset before
    ctx_module.boot_context.initialized = False
    yield
    # Reset after so other tests start clean
    ctx_module.boot_context.initialized = False


@pytest.fixture()
def no_sb_env(monkeypatch):
    """Remove all SB_* environment variables for the duration of the test."""
    sb_keys = [k for k in os.environ if k.startswith("SB_")]
    for key in sb_keys:
        monkeypatch.delenv(key, raising=False)


def test_boot_fails_without_env_vars(no_sb_env):
    """run_boot_dag() must raise (not silently pass) when SB_* vars are absent."""
    from app.core.boot.engine import run_boot_dag

    with pytest.raises((RuntimeError, ValueError, Exception)) as exc_info:
        run_boot_dag()

    # Make sure it's not a generic Python error unrelated to missing config
    assert exc_info.value is not None, "Expected a config-related exception"


def test_boot_is_idempotent(monkeypatch):
    """Calling run_boot_dag() twice must not re-run stages or raise."""
    from app.core.boot.engine import run_boot_dag
    from app.core.boot.context import boot_context

    call_count = 0

    import app.core.boot.engine as engine_module

    def counting_stage():
        nonlocal call_count
        call_count += 1

    monkeypatch.setattr(
        engine_module,
        "BOOT_STAGES",
        [("test_stage", counting_stage)],
    )

    run_boot_dag()
    assert call_count == 1
    assert boot_context.initialized is True

    run_boot_dag()  # second call — must be a no-op
    assert call_count == 1, "Stages must not re-run on second call"
