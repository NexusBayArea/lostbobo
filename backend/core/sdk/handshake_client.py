from __future__ import annotations

from backend.core.protocol.bus.protocol_envelope import ProtocolEnvelope
from backend.core.protocol.bus.protocol_response import ProtocolResponse


async def request_session(
    kernel_bus,
    source_plugin: str,
    target_plugin: str,
    requested_capabilities: list[str],
    tenant_id: str = "system",
) -> str | None:
    envelope = ProtocolEnvelope(
        protocol="a2a_handshake",
        action="request",
        target=target_plugin,
        tenant_id=tenant_id,
        source=source_plugin,
        correlation_id="",
        payload={
            "action": "request",
            "source_plugin_id": source_plugin,
            "target_plugin_id": target_plugin,
            "capabilities": requested_capabilities,
        },
    )
    response: ProtocolResponse = await kernel_bus.dispatch(envelope)
    if response.success:
        return response.payload.get("session_token")
    return None


async def validate_session(kernel_bus, session_token: str) -> dict | None:
    envelope = ProtocolEnvelope(
        protocol="a2a_handshake",
        action="validate",
        target="kernel",
        tenant_id="system",
        source="system",
        correlation_id="",
        payload={"action": "validate", "session_token": session_token},
    )
    response: ProtocolResponse = await kernel_bus.dispatch(envelope)
    if response.success:
        return response.payload
    return None


async def revoke_session(kernel_bus, session_token: str) -> bool:
    envelope = ProtocolEnvelope(
        protocol="a2a_handshake",
        action="revoke",
        target="kernel",
        tenant_id="system",
        source="system",
        correlation_id="",
        payload={"action": "revoke", "session_token": session_token},
    )
    response: ProtocolResponse = await kernel_bus.dispatch(envelope)
    return response.success
