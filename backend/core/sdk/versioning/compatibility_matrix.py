from __future__ import annotations


class CompatibilityMatrix:
    def __init__(self):
        # map (plugin_abi_version, kernel_abi_version) -> compatible?
        self._compatible: dict[tuple[str, str], bool] = {}

    def register(self, plugin_abi: str, kernel_abi: str):
        self._compatible[(plugin_abi, kernel_abi)] = True

    def is_compatible(self, plugin_abi: str, kernel_abi: str) -> bool:
        return self._compatible.get((plugin_abi, kernel_abi), False)
