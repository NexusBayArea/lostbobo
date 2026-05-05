"""Base class for all SimHPC plugins."""

from __future__ import annotations

import abc
from typing import Any


class PluginBase(abc.ABC):
    """All domain plugins must inherit from this."""

    name: str
    version: str = "0.1.0"
    category: str = "domain"  # battery, trading, grid, flood, etc.
    description: str = ""

    @abc.abstractmethod
    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Main execution entrypoint for the plugin."""
        ...

    async def validate_input(self, input_data: dict[str, Any]) -> bool:
        """Optional input validation hook."""
        return True

    async def get_metadata(self) -> dict[str, Any]:
        """Return plugin metadata for UI / registry."""
        return {
            "name": self.name,
            "version": self.version,
            "category": self.category,
            "description": self.description,
        }
