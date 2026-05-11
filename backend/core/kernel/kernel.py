from __future__ import annotations

import logging

from backend.core.sdk.capability_registry import (
    CapabilityRegistry,
)
from backend.core.sdk.dag_node_registry import (
    DAGNodeRegistry,
)
from backend.core.sdk.plugin_loader import (
    PluginLoader,
)


class SimHPCKernel:
    def __init__(self) -> None:
        self.logger = logging.getLogger("simhpc.kernel")

        self.capabilities = CapabilityRegistry()

        self.dag = DAGNodeRegistry()

        self.plugin_loader = PluginLoader(
            kernel=self,
        )

    async def boot(self) -> None:
        self.logger.info("Booting SimHPC Kernel...")

        await self.plugin_loader.load_plugins()

        self.logger.info("Kernel boot complete.")

    async def shutdown(self) -> None:
        self.logger.info("Shutting down SimHPC Kernel...")
        # Placeholder for cleanup logic
        self.logger.info("Kernel shutdown complete.")
