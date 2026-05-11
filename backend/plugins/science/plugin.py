from __future__ import annotations

from backend.core.sdk.base_plugin import (
    BasePlugin,
)
from backend.plugins.science.manifest import (
    manifest,
)


class Plugin(BasePlugin):

    manifest = manifest

    async def register(self, kernel) -> None:

        kernel.capabilities.register(
            "science.reason",
            self.reason,
        )

    async def reason(
        self,
        payload: dict,
    ):

        return {
            "plugin": "science",
            "payload": payload,
        }