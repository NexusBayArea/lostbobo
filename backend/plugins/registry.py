from typing import Dict, Type
from backend.plugins.base import PluginBase

class PluginRegistry:
    _plugins: Dict[str, PluginBase] = {}

    @classmethod
    def register(cls, name: str):
        def decorator(plugin_class: Type[PluginBase]):
            cls._plugins[name] = plugin_class()
            return plugin_class
        return decorator

    @classmethod
    def get(cls, name: str) -> PluginBase:
        if name not in cls._plugins:
            raise ValueError(f"Plugin '{name}' not found.")
        return cls._plugins[name]
