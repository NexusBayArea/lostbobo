# backend/sdk/isolation_router.py
from __future__ import annotations

import logging

log = logging.getLogger(__name__)


class IsolationRouter:
    """Automatic isolation tier selection based on manifest."""

    @staticmethod
    def choose_isolation_mode(manifest: dict) -> str:
        """Auto-tiering based on security tier."""
        tier = manifest.get("security_tier", "standard")
        kata_requested = manifest.get("kata_enabled", False)

        if kata_requested or tier in ("high", "defense"):
            return "kata"
        if tier == "medium" or manifest.get("isolation_mode") == "wasm":
            return "wasm"
        return "sandbox"

    @staticmethod
    def get_runtime_class(mode: str) -> str | None:
        mapping = {
            "kata": "kata-optimized",
            "wasm": None,
            "sandbox": None,
        }
        return mapping.get(mode)


def route_isolation(manifest: dict) -> tuple[str, str | None]:
    """Convenience function returning (mode, runtime_class)."""
    mode = IsolationRouter.choose_isolation_mode(manifest)
    runtime_class = IsolationRouter.get_runtime_class(mode)
    return mode, runtime_class
