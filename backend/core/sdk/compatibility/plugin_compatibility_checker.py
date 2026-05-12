from __future__ import annotations

from backend.core.sdk.versioning.compatibility_matrix import CompatibilityMatrix


class PluginCompatibilityChecker:
    def __init__(self, matrix: CompatibilityMatrix):
        self.matrix = matrix

    def validate(self, plugin_manifest, kernel_abi_version: str) -> bool:
        compatible = self.matrix.is_compatible(plugin_manifest.abi_version, kernel_abi_version)
        if not compatible:
            raise RuntimeError(
                f"Plugin ABI {plugin_manifest.abi_version} incompatible with kernel ABI {kernel_abi_version}"
            )
        return True
