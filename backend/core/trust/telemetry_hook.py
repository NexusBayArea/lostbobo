from __future__ import annotations

import time

from backend.core.runtime.event_fabric.log import EventLogService
from backend.core.runtime.event_fabric.schema import EventPriority, SimHPCEvent


class TrustTelemetry:
    def __init__(self):
        self.event_bus = EventLogService.event_log()

    async def report(self, event_type: str, plugin_id: str, details: dict):
        event = SimHPCEvent(
            event_type=f"trust.{event_type}",
            source_plugin="kernel",
            priority=EventPriority.NORMAL,
            payload={
                "plugin_id": plugin_id,
                "timestamp": time.time(),
                "details": details,
            },
        )
        await self.event_bus.publish(event)
