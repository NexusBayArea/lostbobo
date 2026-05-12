from __future__ import annotations

import secrets
import time
from typing import Any

from backend.core.protocol.bus.protocol_envelope import ProtocolEnvelope
from backend.core.protocol.bus.protocol_response import ProtocolResponse
from backend.core.protocol.contracts.base_protocol import BaseProtocol


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

    def cleanup_expired(self):
        now = time.time()
        expired = [sid for sid, s in self._sessions.items() if s.expires_at <= now]
        for sid in expired:
            self._sessions.pop(sid, None)


class HandshakeProtocol(BaseProtocol):
    protocol_name = "handshake"

    def __init__(self, trust_store, identity_verifier, session_manager):
        self.trust_store = trust_store
        self.identity_verifier = identity_verifier
        self.session_manager = session_manager

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
        requested = payload.get("requested_capabilities", [])

        source = self.trust_store.get_plugin(source_id) if source_id else None
        target = self.trust_store.get_plugin(target_id) if target_id else None

        if not source:
            return ProtocolResponse(success=False, error="source plugin unknown")
        if not target:
            return ProtocolResponse(success=False, error="target plugin unknown")

        if not self.identity_verifier.verify(payload):
            return ProtocolResponse(success=False, error="signature invalid")

        allowed = [c for c in requested if c in target.permissions]
        if not allowed:
            return ProtocolResponse(
                success=False,
                error="no requested capabilities granted by target",
            )

        session_token = self.session_manager.create_session(source_id, target_id, allowed)
        return ProtocolResponse(
            success=True,
            payload={"session_token": session_token, "granted_capabilities": allowed},
        )

    async def _handle_validate(self, payload: dict) -> ProtocolResponse:
        session_token = payload.get("session_token")
        if not session_token:
            return ProtocolResponse(success=False, error="session_token required")

        session = self.session_manager.validate_session(session_token)
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

        self.session_manager.revoke_session(session_token)
        return ProtocolResponse(success=True, payload={"revoked": session_token})
