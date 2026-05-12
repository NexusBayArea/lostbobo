from __future__ import annotations

import secrets
import time


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

    def to_dict(self) -> dict:
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


class TrustedSessionManager:
    """
    Enhanced session manager with:
    - Token-based session lookup (in addition to session_id)
    - Pending handshake state tracking with 5-minute TTL
    - Session revocation and cleanup
    """

    def __init__(self):
        self._sessions: dict[str, Session] = {}  # session_id -> Session
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
            to_remove = [t for t, sid in self._token_index.items() if sid == session_id]
            for token in to_remove:
                del self._token_index[token]

    def revoke_by_token(self, token: str):
        session_id = self._token_index.get(token)
        if session_id:
            self.revoke_session(session_id)

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


# Backward-compatible alias used by kernel_boot.py
SessionManager = TrustedSessionManager
