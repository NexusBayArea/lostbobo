from __future__ import annotations

import importlib
import json
import pkgutil
from pathlib import Path
from typing import Any

from backend.core.sdk.abi.plugin_manifest import (
    PluginManifest,
    PluginPassport,
    PluginPermission,
)
from backend.core.sdk.base_plugin import BasePlugin
from backend.core.sdk.sandbox_manager import SandboxManager
from backend.core.trust.revocation_store import RevocationStore


def load_manifest_from_json(path: Path) -> PluginManifest:
    with open(path) as f:
        data: dict[str, Any] = json.load(f)

    passport_data = data.get("passport")
    passport: PluginPassport | None = None
    if passport_data:
        passport = PluginPassport(**passport_data)

    permission_map = {
        "memory.read": PluginPermission.MEMORY_READ,
        "memory.write": PluginPermission.MEMORY_WRITE,
        "dag.execute": PluginPermission.DAG_EXECUTE,
        "gpu.allocate": PluginPermission.GPU_ALLOCATE,
        "network.egress": PluginPermission.NETWORK_EGRESS,
        "network.outbound": PluginPermission.NETWORK_EGRESS,
        "kernel.events": PluginPermission.KERNEL_EVENTS,
        "lineage.write": PluginPermission.LINEAGE_WRITE,
    }

    permissions = []
    for cap in data.get("capabilities", []):
        mapped = permission_map.get(cap)
        if mapped and mapped not in permissions:
            permissions.append(mapped)

    return PluginManifest(
        name=data.get("name", "unknown"),
        version=data.get("version", "0.0.0"),
        capabilities=data.get("capabilities", []),
        dag_nodes=[],
        permissions=permissions,
        passport=passport,
    )


class PluginLoader:
    def __init__(
        self,
        kernel,
        plugin_package: str = "backend.plugins",
        external_plugin_dirs: list[str] | None = None,
    ) -> None:
        self.kernel = kernel
        self.plugin_package = plugin_package
        self.external_plugin_dirs = external_plugin_dirs or []
        self.sandbox_manager = SandboxManager()
        self.revocation_store = RevocationStore()

    async def load_plugins(self) -> None:
        packages_found = 0
        packages_failed = 0

        for plugin_dir in self.external_plugin_dirs:
            try:
                await self._load_external(Path(plugin_dir))
                packages_found += 1
            except Exception as e:
                print(f"Failed to load external plugin from {plugin_dir}: {e}")
                import traceback

                traceback.print_exc()
                packages_failed += 1

        try:
            package = importlib.import_module(self.plugin_package)
        except Exception as e:
            print(f"Failed to import package {self.plugin_package}: {e}")
            return

        for _, module_name, _ in pkgutil.iter_modules(package.__path__):
            print(f"Found module: {module_name}")
            try:
                await self._load_internal(module_name)
                packages_found += 1
            except Exception as e:
                print(f"Failed to load plugin {module_name}: {e}")
                import traceback

                traceback.print_exc()
                packages_failed += 1

        print(f"Plugin loading complete: {packages_found} loaded, {packages_failed} failed")

    async def _load_external(self, plugin_dir: Path) -> None:
        manifest_path = plugin_dir / "plugin.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"No plugin.json in {plugin_dir}")

        manifest = load_manifest_from_json(manifest_path)
        await self._verify_and_register(manifest)

    async def _load_internal(self, module_name: str) -> None:
        plugin_module = importlib.import_module(f"{self.plugin_package}.{module_name}.plugin")
        plugin_cls = plugin_module.Plugin
        plugin: BasePlugin = plugin_cls()

        manifest = plugin.manifest
        if not isinstance(manifest, PluginManifest):
            raise ValueError(f"{module_name}: no valid PluginManifest")

        await self._verify_and_register(manifest)

        await plugin.register(self.kernel)

    async def _verify_and_register(self, manifest: PluginManifest) -> None:
        if manifest.passport:
            verifier = getattr(self.kernel, "identity_verifier", None)
            if verifier and not verifier.verify_passport(manifest.passport):
                raise PermissionError(f"Plugin {manifest.name}: invalid passport signature")

            if await self.revocation_store.is_revoked(manifest.passport.plugin_id):
                raise PermissionError(f"Plugin {manifest.name}: revoked")

            self.kernel.capabilities.validate(manifest.capabilities, manifest.passport.permissions)

        print(f"  Verified passport for {manifest.name}")

        sandbox = await self.sandbox_manager.create(manifest)
        print(f"  Sandbox {sandbox.sandbox_id} created for {manifest.name}")

        passport_log = ""
        if manifest.passport:
            trust = getattr(self.kernel, "trust_store", None)
            if trust:
                trust.register(manifest.passport)
                passport_log = f" passport={manifest.passport.plugin_id}"

        self.kernel.logger.info(
            "Loaded plugin: %s v%s%s",
            manifest.name,
            manifest.version,
            passport_log,
        )

    async def shutdown(self):
        await self.sandbox_manager.stop_all()
