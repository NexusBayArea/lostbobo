from __future__ import annotations

import importlib
import pkgutil

from backend.core.sdk.abi.plugin_manifest import PluginManifest
from backend.core.sdk.base_plugin import BasePlugin
from backend.core.sdk.sandbox_manager import SandboxManager
from backend.core.trust.revocation_store import RevocationStore


class PluginLoader:
    def __init__(
        self,
        kernel,
        plugin_package: str = "backend.plugins",
    ) -> None:
        self.kernel = kernel
        self.plugin_package = plugin_package
        self.sandbox_manager = SandboxManager()
        self.revocation_store = RevocationStore()

    async def load_plugins(self) -> None:
        packages_found = 0
        packages_failed = 0

        try:
            package = importlib.import_module(self.plugin_package)
        except Exception as e:
            print(f"Failed to import package {self.plugin_package}: {e}")
            return

        for _, module_name, _ in pkgutil.iter_modules(package.__path__):
            print(f"Found module: {module_name}")
            try:
                plugin_module = importlib.import_module(f"{self.plugin_package}.{module_name}.plugin")
                plugin_cls = plugin_module.Plugin
                plugin: BasePlugin = plugin_cls()

                manifest = plugin.manifest
                if not isinstance(manifest, PluginManifest):
                    print(f"  Skipping {module_name}: no valid PluginManifest")
                    packages_failed += 1
                    continue

                if manifest.passport:
                    verifier = getattr(self.kernel, "identity_verifier", None)
                    if verifier and not verifier.verify_passport(manifest.passport):
                        print(f"  REJECTED {module_name}: invalid passport signature")
                        packages_failed += 1
                        continue

                    if await self.revocation_store.is_revoked(manifest.passport.plugin_id):
                        print(f"  REJECTED {module_name}: plugin revoked")
                        packages_failed += 1
                        continue

                print(f"  Verified passport for {manifest.name}")

                sandbox = await self.sandbox_manager.create(manifest)
                print(f"  Sandbox {sandbox.sandbox_id} created for {manifest.name}")

                await plugin.register(self.kernel)

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
                packages_found += 1

            except Exception as e:
                print(f"Failed to load plugin {module_name}: {e}")
                import traceback

                traceback.print_exc()
                packages_failed += 1

        print(f"Plugin loading complete: {packages_found} loaded, {packages_failed} failed")

    async def shutdown(self):
        await self.sandbox_manager.stop_all()
