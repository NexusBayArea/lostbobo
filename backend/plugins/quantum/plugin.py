from __future__ import annotations

from backend.core.sdk.base_plugin import (
    BasePlugin,
)
from backend.plugins.quantum.manifest import (
    manifest,
)


class Plugin(BasePlugin):
    manifest = manifest

    async def register(self, kernel) -> None:
        kernel.capabilities.register(
            "quantum.simulate",
            self.simulate,
        )

    async def simulate(
        self,
        payload: dict,
    ):
        return {
            "plugin": "quantum",
            "payload": payload,
        }
