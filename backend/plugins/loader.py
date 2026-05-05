"""Auto-discovery for plugins — scans backend/plugins/ and registers everything."""

from __future__ import annotations

import importlib
import inspect
import logging
import pkgutil
from pathlib import Path

from backend.plugins.base import PluginBase
from backend.plugins.registry import PluginRegistry

log = logging.getLogger(__name__)


def discover_plugins() -> dict[str, PluginBase]:
    """Automatically find and register all plugins in backend/plugins/."""
    plugins_dir = Path(__file__).parent
    discovered = {}

    for module_info in pkgutil.iter_modules([str(plugins_dir)]):
        if module_info.name.startswith("_"):
            continue

        try:
            # Import the module (e.g. ev_battery.plugin)
            full_module_name = f"backend.plugins.{module_info.name}"
            module = importlib.import_module(full_module_name)

            # Look for classes that inherit from PluginBase
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, PluginBase) and obj is not PluginBase:
                    # Register via decorator-style (or direct)
                    plugin_name = getattr(obj, "name", name.lower())
                    PluginRegistry.register(plugin_name)(obj)
                    discovered[plugin_name] = obj()
                    log.info(f"Auto-discovered plugin: {plugin_name}")

        except Exception as e:
            log.warning(f"Failed to load plugin module {module_info.name}: {e}")

    return discovered


# Run discovery on import
_discovered_plugins = discover_plugins()
