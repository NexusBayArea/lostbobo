from __future__ import annotations

from abc import ABC, abstractmethod

from backend.core.protocol.bus.protocol_envelope import ProtocolEnvelope
from backend.core.protocol.bus.protocol_response import ProtocolResponse


class BaseProtocol(ABC):
    protocol_name: str

    @abstractmethod
    async def handle(self, envelope: ProtocolEnvelope) -> ProtocolResponse: ...
