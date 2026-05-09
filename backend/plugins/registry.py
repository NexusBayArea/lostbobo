"""Plugin Registry with auto-discovery and lifecycle management."""

from __future__ import annotations

import asyncio
import importlib
import logging
import pkgutil
from pathlib import Path

from backend.plugins.base import PluginBase

log = logging.getLogger(__name__)


class PluginRegistry:
    _instance = None
    _plugins: dict[str, PluginBase] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_plugins()
        return cls._instance

    @classmethod
    def registry(cls) -> PluginRegistry:
        return cls()

    def _load_plugins(self) -> None:
        plugins_dir = Path(__file__).parent
        for module_info in pkgutil.iter_modules([str(plugins_dir)]):
            if module_info.name.startswith("_"):
                continue
            try:
                mod = importlib.import_module(f"backend.plugins.{module_info.name}")
                for _name, obj in vars(mod).items():
                    if isinstance(obj, type) and issubclass(obj, PluginBase) and obj is not PluginBase:
                        plugin = obj()
                        self._plugins[plugin.name] = plugin
                        if plugin.enabled:
                            asyncio.create_task(plugin.initialize())
                        log.info("Loaded plugin: %s v%s", plugin.name, plugin.version)
            except Exception as exc:
                log.warning("Failed to load plugin %s: %s", module_info.name, exc)

    def get(self, name: str) -> PluginBase | None:
        return self._plugins.get(name)

    def list_all(self) -> list[str]:
        return list(self._plugins.keys())

    def get_by_category(self, category: str) -> list[PluginBase]:
        return [p for p in self._plugins.values() if getattr(p, "category", None) == category]
