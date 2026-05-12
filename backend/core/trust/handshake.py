from __future__ import annotations

import secrets
import time
from typing import Any

from backend.core.protocol.bus.protocol_envelope import ProtocolEnvelope
from backend.core.protocol.bus.protocol_response import ProtocolResponse
from backend.core.protocol.contracts.base_protocol import BaseProtocol
from backend.core.trust.behavioral_engine import BehavioralTrustEvaluator, TrustScoreBreakdown
from backend.core.trust.identity import TrustVerifier
from backend.core.trust.session_manager import TrustedSessionManager


class Session:
    def __init__(
        self,
        session_id: str,
        source_plugin: str,
        target_plugin: str,
        capabilities: list[str],
        ttl_seconds: int = 300,
        trust_score: float = 1.0,
        action: str = "allow",
    ):
        self.session_id = session_id
        self.source_plugin = source_plugin
        self.target_plugin = target_plugin
        self.capabilities = capabilities
        self.trust_score = trust_score
        self.action = action
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
            "trust_score": self.trust_score,
            "action": self.action,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
        }


class SessionManager:
    def __init__(self):
        self._sessions: dict[str, Session] = {}
        self._token_index: dict[str, str] = {}  # token -> session_id
        self._pending_handshakes: dict[tuple, dict] = {}  # (source, target) -> {nonce, timestamp}

    def create_session(
        self,
        source: str,
        target: str,
        capabilities: list[str],
        ttl_seconds: int = 300,
        trust_score: float = 1.0,
        action: str = "allow",
    ) -> dict:
        session_id = secrets.token_hex(16)
        token = secrets.token_hex(32)
        session = Session(
            session_id=session_id,
            source_plugin=source,
            target_plugin=target,
            capabilities=capabilities,
            ttl_seconds=ttl_seconds,
            trust_score=trust_score,
            action=action,
        )
        self._sessions[session_id] = session
        self._token_index[token] = session_id
        return {
            "session_id": session_id,
            "token": token,
            "expires_at": session.expires_at,
        }

    def validate_session(self, session_id: str) -> Session | None:
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if session.is_expired():
            self._sessions.pop(session_id, None)
            return None
        return session

    def get_by_token(self, token: str) -> Session | None:
        session_id = self._token_index.get(token)
        if session_id is None:
            return None
        return self.validate_session(session_id)

    def revoke_session(self, session_id: str):
        session = self._sessions.pop(session_id, None)
        if session:
            for token, sid in list(self._token_index.items()):
                if sid == session_id:
                    del self._token_index[token]
                    break

    def is_valid(self, session_token: str) -> bool:
        return self.get_by_token(session_token) is not None

    def get_target(self, session_token: str) -> str | None:
        session = self.get_by_token(session_token)
        if session is None:
            return None
        return session.target_plugin

    def cleanup_expired(self):
        now = time.time()
        expired = [sid for sid, s in self._sessions.items() if s.expires_at <= now]
        for sid in expired:
            self.revoke_session(sid)

    def set_pending_handshake(self, source: str, target: str, nonce: str):
        self._pending_handshakes[(source, target)] = {
            "nonce": nonce,
            "timestamp": time.time(),
        }

    def get_pending_handshake(self, source: str, target: str) -> dict | None:
        entry = self._pending_handshakes.get((source, target))
        if entry is None:
            return None
        if (time.time() - entry["timestamp"]) > 300:
            self._pending_handshakes.pop((source, target), None)
            return None
        return entry

    def clear_pending_handshake(self, source: str, target: str):
        self._pending_handshakes.pop((source, target), None)


class A2AHandshakeProtocol(BaseProtocol):
    """
    Full multi-step Agent-to-Agent handshake state machine.
    Steps: HELLO → CHALLENGE → CHALLENGE_RESPONSE → RESULT
    """

    protocol_name = "a2a_handshake"
    HELLO = "hello"
    CHALLENGE = "challenge"
    CHALLENGE_RESPONSE = "challenge_response"
    RESULT = "result"

    def __init__(self, kernel):
        self.kernel = kernel
        self.verifier = TrustVerifier(kernel)

        graph_store = getattr(kernel.memory_fabric, "graph_store", None) if hasattr(kernel, "memory_fabric") else None
        world_fabric = getattr(kernel, "world_fabric", None)
        event_store = getattr(kernel, "event_store", None)
        anomaly_detector = getattr(kernel, "anomaly_detector", None)

        from backend.core.trust.telemetry_hook import TrustTelemetry

        self.evaluator = BehavioralTrustEvaluator(
            event_store,
            anomaly_detector,
            graph_store,
            world_fabric,
        )
        self.sessions = TrustedSessionManager()
        self.telemetry = TrustTelemetry(getattr(kernel, "event_bus", None))

    async def handle(self, envelope: ProtocolEnvelope) -> ProtocolResponse:
        step = envelope.payload.get("step")
        if step == self.HELLO:
            return await self._handle_hello(envelope)
        elif step == self.CHALLENGE_RESPONSE:
            return await self._handle_challenge_response(envelope)
        else:
            return ProtocolResponse(success=False, error=f"Unknown handshake step: {step}")

    async def _handle_hello(self, envelope: ProtocolEnvelope) -> ProtocolResponse:
        payload = envelope.payload
        source_id = payload["plugin_id"]
        target_id = payload.get("target_plugin_id")
        if not target_id:
            return ProtocolResponse(success=False, error="Missing target_plugin_id")

        # 1. Retrieve plugin passports
        source = self.kernel.trust_store.get_plugin(source_id)
        target = self.kernel.trust_store.get_plugin(target_id)
        if not source or not target:
            return ProtocolResponse(success=False, error="Plugin not found")

        # 2. Verify signature of HELLO packet
        if not self.verifier.verify_request(payload, source.public_key):
            return ProtocolResponse(success=False, error="Invalid signature")

        # 3. Generate challenge (nonce)
        challenge_nonce = secrets.token_hex(32)
        self.kernel.session_manager.set_pending_handshake(source_id, target_id, challenge_nonce)

        await self.telemetry.report(
            "handshake.hello_received",
            source_id,
            {
                "target": target_id,
                "step": self.HELLO,
            },
        )
        return ProtocolResponse(
            success=True,
            payload={
                "step": self.CHALLENGE,
                "challenge_nonce": challenge_nonce,
                "target_plugin_id": target_id,
            },
        )

    async def _handle_challenge_response(self, envelope: ProtocolEnvelope) -> ProtocolResponse:
        payload = envelope.payload
        source_id = payload["plugin_id"]
        target_id = payload["target_plugin_id"]
        challenge_nonce = payload["challenge_nonce"]
        signed_nonce = payload["signed_nonce"]
        runtime_attestation = payload.get("runtime_attestation", {})

        # 1. Validate pending handshake exists
        pending = self.kernel.session_manager.get_pending_handshake(source_id, target_id)
        if not pending or pending["nonce"] != challenge_nonce:
            return ProtocolResponse(success=False, error="Invalid or expired challenge")

        # 2. Verify signed nonce with target's public key
        target = self.kernel.trust_store.get_plugin(target_id)
        if not self.verifier.verify_challenge_response(target, challenge_nonce, signed_nonce):
            return ProtocolResponse(success=False, error="Challenge response invalid")

        # 3. Runtime attestation checks (sandbox, container hash)
        if not runtime_attestation.get("sandbox", False):
            return ProtocolResponse(success=False, error="Plugin not running in required sandbox")
        expected_hash = self.verifier.get_expected_container_hash(target_id)
        if expected_hash and runtime_attestation.get("container_hash") != expected_hash:
            return ProtocolResponse(success=False, error="Container hash mismatch")

        # 4. Behavioral trust evaluation
        trust_result: TrustScoreBreakdown = await self.evaluator.evaluate(
            source_id=source_id,
            target_id=target_id,
            identity_ok=True,
            capabilities_ok=True,
        )

        # 5. Capability validation against target's policy
        requested = payload.get("requested_capabilities", [])
        allowed = []
        restrictions = []
        for cap in requested:
            if self.kernel.policy_engine.is_capability_allowed(target_id, cap):
                allowed.append(cap)
            else:
                restrictions.append(f"{cap}.denied")

        # 6. Issue session token with trust score and capabilities
        session_result = self.sessions.create_session(
            source_id,
            target_id,
            allowed,
            trust_score=trust_result.trust_score,
            action=trust_result.action,
            ttl_seconds=3600,
        )

        # Store session in kernel's session manager for cross-protocol use
        self.kernel.session_manager._sessions[session_result["session_id"]] = self.sessions._sessions.get(
            session_result["token"]
        )
        self.kernel.session_manager._token_index[session_result["token"]] = session_result["session_id"]

        await self.telemetry.report(
            "handshake.completed",
            source_id,
            {
                "target": target_id,
                "trust_score": trust_result.trust_score,
                "session_id": session_result["session_id"],
                "step": self.RESULT,
            },
        )

        return ProtocolResponse(
            success=True,
            payload={
                "step": self.RESULT,
                "verified": True,
                "trust_score": trust_result.trust_score,
                "session_token": session_result["token"],
                "expires_in": 3600,
                "allowed_capabilities": allowed,
                "restrictions": restrictions,
            },
        )

    async def validate(self, payload: dict) -> ProtocolResponse:
        session_token = payload.get("session_token")
        if not session_token:
            return ProtocolResponse(success=False, error="session_token required")
        session = self.sessions.get_by_token(session_token)
        if session is None:
            return ProtocolResponse(success=False, error="session invalid or expired")
        return ProtocolResponse(success=True, payload=session.to_dict())

    async def revoke(self, payload: dict) -> ProtocolResponse:
        session_token = payload.get("session_token")
        if not session_token:
            return ProtocolResponse(success=False, error="session_token required")
        self.sessions.revoke_session(session_token)
        return ProtocolResponse(success=True, payload={"revoked": session_token})
