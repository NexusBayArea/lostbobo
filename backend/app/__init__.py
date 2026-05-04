"""
SimHPC App Package
==================

Core FastAPI application, routers, and business logic.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

__all__ = ["app", "create_app"]

def create_app() -> "FastAPI":
    """Factory function to create the SimHPC application."""
    from .main import app
    return app


# Lazy import for convenience
def __getattr__(name: str):
    if name == "app":
        from .main import app
        return app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
