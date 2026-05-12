"""
JIT Runtime Loader for deterministic GPU execution.
Libraries must be pre-installed in the container image.
This module validates and imports them on demand.
"""

from __future__ import annotations

import importlib


class RuntimeLoader:
    def __init__(self):
        self._cache: dict[str, object] = {}

    def load(self, required_libraries: list[str] | None = None) -> dict[str, object]:
        if required_libraries is None:
            required_libraries = []

        loaded = {}
        for lib in required_libraries:
            if lib not in self._cache:
                try:
                    mod = importlib.import_module(lib)
                    self._cache[lib] = mod
                except ImportError as e:
                    raise ImportError(
                        f"Required library '{lib}' is not available in this GPU runtime. "
                        f"Please bake it into the container image. Error: {e}"
                    ) from e
            loaded[lib] = self._cache[lib]
        return loaded
