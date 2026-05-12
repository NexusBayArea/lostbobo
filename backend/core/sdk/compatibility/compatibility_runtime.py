from __future__ import annotations

from backend.core.sdk.compatibility.plugin_compatibility_checker import PluginCompatibilityChecker


class CompatibilityRuntime:
    def __init__(self, checker: PluginCompatibilityChecker, kernel_abi: str):
        self.checker = checker
        self.kernel_abi = kernel_abi

    def validate_plugin(self, plugin_manifest) -> bool:
        return self.checker.validate(plugin_manifest, self.kernel_abi)
