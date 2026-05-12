from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from backend.core.runtime.event_fabric.log import EventLogService
from backend.core.runtime.event_fabric.schema import EventPriority, SimHPCEvent


class SimulationEvent(BaseModel):
    execution_id: str
    event_type: str
    timestamp: float = Field(default_factory=time.time)
    data: Dict[str, Any] = Field(default_factory=dict)


class SimulationStreamManager:
    def __init__(self, event_bus: Optional[EventLogService] = None):
        self.event_bus = event_bus or EventLogService.event_log()
        self._active_streams: Dict[str, asyncio.Queue] = {}

    async def start_stream(self, execution_id: str):
        if execution_id not in self._active_streams:
            self._active_streams[execution_id] = asyncio.Queue()

    async def push_event(self, execution_id: str, event: SimulationEvent):
        if execution_id in self._active_streams:
            await self._active_streams[execution_id].put(event)

        simhpc_event = SimHPCEvent(
            event_type=f"execution.{event.event_type}",
            source_plugin="execution",
            priority=EventPriority.NORMAL,
            payload=event.model_dump(),
        )
        await self.event_bus.publish(simhpc_event)

    async def get_stream(self, execution_id: str) -> Optional[asyncio.Queue]:
        return self._active_streams.get(execution_id)

    async def stop_stream(self, execution_id: str):
        self._active_streams.pop(execution_id, None)
