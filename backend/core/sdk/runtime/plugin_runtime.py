from __future__ import annotations

from backend.core.sdk.registries.capability_registry import CapabilityRegistry
from backend.core.sdk.registries.dag_registry import DAGNodeRegistry
from backend.core.sdk.registries.plugin_registry import PluginRegistry
from backend.core.sdk.runtime.plugin_context import PluginContext


class PluginRuntime:
    def __init__(self, kernel=None):
        self.kernel = kernel
        self.capability_registry = CapabilityRegistry()
        self.dag_registry = DAGNodeRegistry()
        self.plugin_registry = PluginRegistry()

    async def boot_plugin(self, plugin) -> PluginContext:
        from backend.core.sdk.runtime.plugin_bootstrapper import PluginBootstrapper

        bootstrapper = PluginBootstrapper(
            capability_registry=self.capability_registry,
            dag_registry=self.dag_registry,
            plugin_registry=self.plugin_registry,
        )
        ctx = await bootstrapper.boot_plugin(plugin.manifest)

        if self.kernel:
            self.kernel.logger.info("Plugin booted: %s", plugin.manifest.name)

        return ctx

    async def shutdown(self):
        for plugin_name in self.plugin_registry.list_running():
            ctx = self.plugin_registry.get_context(plugin_name)
            if ctx and ctx.plugin_instance:
                if hasattr(ctx.plugin_instance, "shutdown"):
                    await ctx.plugin_instance.shutdown()
            self.plugin_registry.unregister(plugin_name)
