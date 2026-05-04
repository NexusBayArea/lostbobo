"""
SimHPC Backend Package
======================

Production-ready GPU-accelerated finite element simulation platform
with robustness analysis, AI engineering reports, and enterprise features.
"""

__version__ = "3.5.1"
__author__ = "neXusEvents / SimHPC Team"
__description__ = "SimHPC Backend - Orchestrator, Runtime & Physics Engine"

# Public API exports
__all__ = [
    "version",
    "app",
    "runtime",
    "KERNEL",
    "CONTRACT",
]

# Version access
def version() -> str:
    """Return the current backend version."""
    return __version__


# Lazy imports for convenience (optional but clean)
def __getattr__(name: str):
    """Lazy loading of major components."""
    if name == "app":
        from .app.main import app
        return app
    elif name == "runtime":
        import backend.runtime
        return backend.runtime
    elif name == "KERNEL":
        from .runtime.kernel import KERNEL
        return KERNEL
    elif name == "CONTRACT":
        from .runtime.contract import CONTRACT
        return CONTRACT
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# Package metadata for introspection
__metadata__ = {
    "name": "simhpc-backend",
    "version": __version__,
    "description": __description__,
    "python_requires": ">=3.11",
}
