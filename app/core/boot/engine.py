"""Deterministic Boot DAG Engine."""
import logging

from app.core.boot.context import boot_context
from app.core.boot.stages.env import load_env
from app.core.boot.stages.validate import validate_env
from app.core.boot.stages.normalize import normalize
from app.core.boot.stages.config import build_settings

logger = logging.getLogger(__name__)

# Deterministic boot pipeline - ORDER MATTERS
BOOT_STAGES = [
    ("env_load", load_env),
    ("validation", validate_env),
    ("normalization", normalize),
    ("config_build", build_settings),
]


def run_boot_dag():
    """
    Execute deterministic boot pipeline.

    This is the ONLY place where runtime initialization happens.
    All modules import this after boot completes.

    Idempotent: safe to call multiple times (subsequent calls are no-ops).
    """
    # FIX: idempotency guard — prevents double-init in tests and re-entrant calls
    if boot_context.initialized:
        logger.debug("[BOOT] Already initialized, skipping.")
        return

    logger.info("[BOOT] Starting deterministic boot DAG...")

    for stage_name, stage_func in BOOT_STAGES:
        try:
            logger.info("[BOOT] Stage: %s", stage_name)
            stage_func()
        except Exception as e:
            logger.error("[BOOT FAILURE] Stage '%s' failed: %s", stage_name, e)
            raise

    boot_context.initialized = True
    logger.info("[BOOT] Complete. Context initialized.")


def get_boot_context():
    """Get the initialized boot context."""
    if not boot_context.initialized:
        raise RuntimeError(
            "Boot context not initialized. "
            "Call run_boot_dag() before accessing config."
        )
    return boot_context
