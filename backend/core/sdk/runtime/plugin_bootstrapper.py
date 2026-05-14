from __future__ import annotations

import importlib
import json
from pathlib import Path

from backend.core.sdk.abi.lifecycle import PluginState
from backend.core.sdk.abi.permissions import PermissionSet, Syscall
from backend.core.sdk.abi.plugin_manifest import PluginManifest
from backend.core.sdk.registries.capability_registry import CapabilityRegistry
from backend.core.sdk.registries.dag_registry import DAGNodeRegistry
from backend.core.sdk.registries.plugin_registry import PluginRegistry
from backend.core.sdk.runtime.plugin_context import PluginContext


class PluginBootstrapper:
    def __init__(
        self,
        capability_registry: CapabilityRegistry,
        dag_registry: DAGNodeRegistry,
        plugin_registry: PluginRegistry,
    ):
        self.capability_registry = capability_registry
        self.dag_registry = dag_registry
        self.plugin_registry = plugin_registry
        self.contexts: dict[str, PluginContext] = {}

    async def discover_and_load(self, plugins_path: str | None = None) -> list[PluginContext]:
        if plugins_path is None:
            plugins_path = str(Path(__file__).resolve().parent.parent.parent.parent / "plugins")

        manifests = await self._discover_manifests(plugins_path)
        sorted_manifests = self._topological_sort(manifests)

        booted = []
        for manifest in sorted_manifests:
            ctx = await self.boot_plugin(manifest)
            booted.append(ctx)
        return booted

    async def boot_plugin(self, manifest: PluginManifest) -> PluginContext:
        self._validate_sdk_compatibility(manifest)

        ctx = PluginContext(
            plugin_name=manifest.name,
            manifest_version=manifest.version,
        )

        ctx.permissions = PermissionSet(
            allowed_syscalls={Syscall(s.name) for s in manifest.permissions.syscalls},
            syscall_constraints={},
            network_rules=manifest.permissions.network_egress,
            secret_scopes=manifest.permissions.secrets,
            delegated_capabilities=set(manifest.permissions.capabilities_delegate),
        )
        ctx.isolation_tier = manifest.isolation_tier.value

        ctx.lifecycle.transition(PluginState.INITIALIZING, reason="Boot started")

        plugin_module = importlib.import_module(f"backend.plugins.{manifest.name}.plugin")
        plugin_instance = plugin_module.plugin
        ctx.plugin_instance = plugin_instance

        kernel_bridge = _KernelBridge(
            capability_registry=self.capability_registry,
            dag_registry=self.dag_registry,
        )
        await plugin_instance.register(kernel_bridge)

        ctx.lifecycle.transition(PluginState.RUNNING, reason="Boot complete")

        self.plugin_registry.register(ctx)
        self.contexts[manifest.name] = ctx

        return ctx

    def _validate_sdk_compatibility(self, manifest: PluginManifest) -> None:  # noqa: ARG002
        pass

    async def _discover_manifests(self, plugins_path: str) -> list[PluginManifest]:
        manifests = []
        plugins_dir = Path(plugins_path)
        if not plugins_dir.exists():
            return manifests
        for plugin_dir in plugins_dir.iterdir():
            if plugin_dir.is_dir() and not plugin_dir.name.startswith("_"):
                manifest_path = plugin_dir / "manifest.json"
                if manifest_path.exists():
                    with open(manifest_path) as f:
                        data = json.load(f)
                    manifests.append(PluginManifest(**data))
        return manifests

    def _topological_sort(self, manifests: list[PluginManifest]) -> list[PluginManifest]:
        name_map = {m.name: m for m in manifests}
        sorted_manifests = []
        visited = set()

        def visit(name: str):
            if name in visited:
                return
            visited.add(name)
            manifest = name_map.get(name)
            if manifest:
                for dep in manifest.depends_on_plugins:
                    if dep not in visited:
                        visit(dep)
                sorted_manifests.append(manifest)

        for m in manifests:
            visit(m.name)

        return sorted_manifests


class _KernelBridge:
    def __init__(
        self,
        capability_registry: CapabilityRegistry,
        dag_registry: DAGNodeRegistry,
    ):
        self.capability_registry = capability_registry
        self.dag_registry = dag_registry
