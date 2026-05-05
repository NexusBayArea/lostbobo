"""Plugin Registry with auto-discovery support."""

from __future__ import annotations

from backend.plugins.base import PluginBase


class PluginRegistry:
    _plugins: dict[str, PluginBase] = {}

    @classmethod
    def register(cls, name: str):
        def decorator(plugin_class: type[PluginBase]):
            instance = plugin_class()
            cls._plugins[name] = instance
            print(f"Plugin registered: {name} ({plugin_class.__name__})")
            return plugin_class

        return decorator

    @classmethod
    def get(cls, name: str) -> PluginBase:
        if name not in cls._plugins:
            raise ValueError(f"Plugin '{name}' not found. Available: {list(cls._plugins.keys())}")
        return cls._plugins[name]

    @classmethod
    def list_all(cls) -> list[str]:
        return list(cls._plugins.keys())

    @classmethod
    def get_by_category(cls, category: str) -> list[PluginBase]:
        return [p for p in cls._plugins.values() if getattr(p, "category", None) == category]
