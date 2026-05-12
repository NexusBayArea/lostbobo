from __future__ import annotations

from backend.core.protocol.bus.protocol_envelope import ProtocolEnvelope
from backend.core.protocol.bus.protocol_response import ProtocolResponse
from backend.core.protocol.contracts.base_protocol import BaseProtocol


class PluginMessageProtocol(BaseProtocol):
    protocol_name = "plugin_message"

    def __init__(self, kernel):
        self.kernel = kernel

    async def handle(self, envelope: ProtocolEnvelope) -> ProtocolResponse:
        session_token = envelope.metadata.get("session_token")
        if not session_token:
            return ProtocolResponse(success=False, error="session_token required in metadata")

        if not self.kernel.session_manager.is_valid(session_token):
            return ProtocolResponse(success=False, error="Invalid or expired session")

        target_plugin = self.kernel.session_manager.get_target(session_token)
        if target_plugin is None:
            return ProtocolResponse(success=False, error="No target for session")

        capability = envelope.payload.get("capability")
        if not capability:
            return ProtocolResponse(success=False, error="capability required in payload")

        payload = envelope.payload.get("payload", {})
        try:
            result = await self.kernel.capabilities.invoke(capability, payload)
            return ProtocolResponse(success=True, payload={"result": result})
        except KeyError:
            return ProtocolResponse(success=False, error=f"capability {capability} not found on target")
        except Exception as e:
            return ProtocolResponse(success=False, error=str(e))
