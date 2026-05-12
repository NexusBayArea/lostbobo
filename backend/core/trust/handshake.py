from __future__ import annotations

import secrets
import time
from typing import Any

from backend.core.protocol.bus.protocol_envelope import ProtocolEnvelope
from backend.core.protocol.bus.protocol_response import ProtocolResponse
from backend.core.protocol.contracts.base_protocol import BaseProtocol
from backend.core.trust.identity import TrustVerifier


class Session:
    def __init__(
        self,
        session_id: str,
        source_plugin: str,
        target_plugin: str,
        capabilities: list[str],
        ttl_seconds: int = 300,
    ):
        self.session_id = session_id
        self.source_plugin = source_plugin
        self.target_plugin = target_plugin
        self.capabilities = capabilities
        self.created_at = time.time()
        self.expires_at = time.time() + ttl_seconds

    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "source_plugin": self.source_plugin,
            "target_plugin": self.target_plugin,
            "capabilities": self.capabilities,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
        }


class SessionManager:
    def __init__(self):
        self._sessions: dict[str, Session] = {}

    def create_session(
        self,
        source: str,
        target: str,
        capabilities: list[str],
        ttl_seconds: int = 300,
    ) -> str:
        session_id = secrets.token_hex(16)
        session = Session(session_id, source, target, capabilities, ttl_seconds)
        self._sessions[session_id] = session
        return session_id

    def validate_session(self, session_id: str) -> Session | None:
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if session.is_expired():
            self._sessions.pop(session_id, None)
            return None
        return session

    def revoke_session(self, session_id: str):
        self._sessions.pop(session_id, None)

    def is_valid(self, session_token: str) -> bool:
        session = self._sessions.get(session_token)
        if session is None:
            return False
        if session.is_expired():
            self._sessions.pop(session_token, None)
            return False
        return True

    def get_target(self, session_token: str) -> str | None:
        session = self._sessions.get(session_token)
        if session is None or session.is_expired():
            return None
        return session.target_plugin

    def cleanup_expired(self):
        now = time.time()
        expired = [sid for sid, s in self._sessions.items() if s.expires_at <= now]
        for sid in expired:
            self._sessions.pop(sid, None)


class HandshakeProtocol(BaseProtocol):
    protocol_name = "a2a_handshake"

    def __init__(self, kernel):
        self.kernel = kernel
        self.verifier = TrustVerifier(kernel)
        self.telemetry = kernel.trust_telemetry

    async def handle(self, envelope: ProtocolEnvelope) -> ProtocolResponse:
        payload = envelope.payload
        action = payload.get("action", "request")

        if action == "request":
            return await self._handle_request(payload)
        elif action == "validate":
            return await self._handle_validate(payload)
        elif action == "revoke":
            return await self._handle_revoke(payload)
        else:
            return ProtocolResponse(success=False, error=f"Unknown handshake action: {action}")

    async def _handle_request(self, payload: dict) -> ProtocolResponse:
        source_id = payload.get("source_plugin_id")
        target_id = payload.get("target_plugin_id")
        requested = payload.get("capabilities", payload.get("requested_capabilities", []))
        payload.get("nonce")

        trust_store = self.kernel.trust_store
        source = trust_store.get_plugin(source_id) if source_id else None
        target = trust_store.get_plugin(target_id) if target_id else None

        if not source:
            await self.telemetry.report(
                "handshake.failed", source_id or "unknown", {"reason": "source not found", "target": target_id}
            )
            return ProtocolResponse(success=False, error="Source plugin not found")
        if not target:
            await self.telemetry.report("handshake.failed", target_id or "unknown", {"reason": "target not found"})
            return ProtocolResponse(success=False, error="Target plugin not found")

        if not self.verifier.verify_request(payload, source.public_key):
            await self.telemetry.report("handshake.invalid_signature", source_id, {"target": target_id})
            return ProtocolResponse(success=False, error="Invalid request signature")

        for cap in requested:
            if cap not in source.permissions:
                await self.telemetry.report("handshake.unauthorized_capability", source_id, {"requested": cap})
                return ProtocolResponse(success=False, error=f"Capability {cap} not allowed for source")

        for cap in requested:
            if cap not in target.permissions:
                await self.telemetry.report("handshake.unauthorized_capability", target_id, {"requested": cap})
                return ProtocolResponse(success=False, error=f"Capability {cap} not available on target")

        if payload.get("mutual_challenge"):
            challenge = self.verifier.generate_challenge(target_id)
            try:
                response = await self._challenge_plugin(target_id, challenge)
                if not self.verifier.verify_challenge_response(target_id, response):
                    return ProtocolResponse(success=False, error="Target plugin challenge failed")
            except Exception:
                return ProtocolResponse(success=False, error="Plugin challenge timeout")

        session_id = self.kernel.session_manager.create_session(source_id, target_id, requested)
        session = self.kernel.session_manager.validate_session(session_id)

        await self.telemetry.report("handshake.completed", source_id, {"target": target_id, "session_id": session_id})

        return ProtocolResponse(
            success=True,
            payload={
                "session_token": session_id,
                "expires_at": session.expires_at if session else 0,
                "granted_capabilities": requested,
            },
        )

    async def _challenge_plugin(self, plugin_id: str, challenge: str) -> str:
        return "signed_response"

    async def _handle_validate(self, payload: dict) -> ProtocolResponse:
        session_token = payload.get("session_token")
        if not session_token:
            return ProtocolResponse(success=False, error="session_token required")

        session = self.kernel.session_manager.validate_session(session_token)
        if session is None:
            return ProtocolResponse(success=False, error="session invalid or expired")

        return ProtocolResponse(
            success=True,
            payload=session.to_dict(),
        )

    async def _handle_revoke(self, payload: dict) -> ProtocolResponse:
        session_token = payload.get("session_token")
        if not session_token:
            return ProtocolResponse(success=False, error="session_token required")

        self.kernel.session_manager.revoke_session(session_token)
        return ProtocolResponse(success=True, payload={"revoked": session_token})
