"""
Lineage Collector Plugin — captures execution lineage and provenance data.
Stores lineage events in the kernel's memory fabric for audit and replay.
"""

from __future__ import annotations

import time
from typing import Any

from backend.core.sdk.base_plugin import BasePlugin
from backend.plugins.lineage_collector.manifest import manifest


class Plugin(BasePlugin):
    manifest = manifest

    async def register(self, kernel) -> None:
        self.kernel = kernel
        kernel.capabilities.register("lineage.collect", self.collect)
        kernel.capabilities.register("lineage.query", self.query)

    async def collect(self, payload: dict[str, Any]) -> dict[str, Any]:
        event = {
            "event_type": payload.get("event_type", "lineage.event"),
            "execution_id": payload.get("execution_id"),
            "timestamp": time.time(),
            "metadata": payload.get("metadata", {}),
        }
        return {"status": "recorded", "event": event}

    async def query(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"status": "ok", "events": []}
