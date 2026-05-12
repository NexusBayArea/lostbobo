from __future__ import annotations

from backend.core.protocol.bus.protocol_response import ProtocolResponse
from backend.core.protocol.contracts.base_protocol import BaseProtocol


class EventProtocol(BaseProtocol):
    protocol_name = "event"

    async def handle(self, envelope):
        # publish event logic
        return ProtocolResponse(
            success=True,
            payload={
                "event_processed": True,
            },
        )
