from __future__ import annotations

import importlib
import pkgutil

from backend.core.sdk.base_plugin import BasePlugin


class PluginLoader:
    def __init__(
        self,
        kernel,
        plugin_package: str = "backend.plugins",
    ) -> None:
        self.kernel = kernel
        self.plugin_package = plugin_package

    async def load_plugins(self) -> None:
        print(f"Loading plugins from package: {self.plugin_package}")

        try:
            package = importlib.import_module(self.plugin_package)
            print(f"Successfully imported package: {self.plugin_package}")
            print(f"Package path: {package.__path__}")
        except Exception as e:
            print(f"Failed to import package {self.plugin_package}: {e}")
            return

        for _, module_name, _ in pkgutil.iter_modules(package.__path__):
            print(f"Found module: {module_name}")
            try:
                plugin_module = importlib.import_module(f"{self.plugin_package}.{module_name}.plugin")
                print(f"Successfully imported plugin module: {self.plugin_package}.{module_name}.plugin")

                plugin_cls = plugin_module.Plugin
                print(f"Found Plugin class in {module_name}")

                plugin: BasePlugin = plugin_cls()
                print(f"Created plugin instance: {plugin.__class__.__name__}")

                await plugin.register(self.kernel)
                print(f"Registered plugin: {plugin.manifest.name}")

                self.kernel.logger.info(
                    "Loaded plugin: %s",
                    plugin.manifest.name,
                )
            except Exception as e:
                print(f"Failed to load plugin {module_name}: {e}")
                import traceback

                traceback.print_exc()
