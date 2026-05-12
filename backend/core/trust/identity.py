from __future__ import annotations

import hashlib
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa, utils

from backend.core.sdk.abi.plugin_manifest import PluginPassport


class TrustError(Exception):
    """Raised when a plugin trust check fails (signature, revocation, capability)."""


class TrustStore:
    def __init__(self):
        self._plugins: dict[str, PluginPassport] = {}

    def register(self, passport: PluginPassport):
        self._plugins[passport.plugin_id] = passport

    def get_plugin(self, plugin_id: str) -> PluginPassport | None:
        return self._plugins.get(plugin_id)

    def remove(self, plugin_id: str):
        self._plugins.pop(plugin_id, None)

    def list_plugins(self) -> list[PluginPassport]:
        return list(self._plugins.values())


class IdentityVerifier:
    def verify(self, payload: dict[str, Any]) -> bool:
        signature_hex = payload.get("signature")
        data = payload.get("data", {})
        public_key_pem = payload.get("public_key")

        if not signature_hex or not public_key_pem:
            return False

        try:
            public_key = serialization.load_pem_public_key(public_key_pem.encode())
            if not isinstance(public_key, rsa.RSAPublicKey):
                return False

            signature = bytes.fromhex(signature_hex)
            message = self._canonical_json(data).encode()

            public_key.verify(
                signature,
                message,
                padding.PKCS1v15(),
                utils.Prehashed(hashes.SHA256()),
            )
            return True
        except (InvalidSignature, Exception):
            return False

    def verify_passport(self, passport: PluginPassport) -> bool:
        try:
            public_key = serialization.load_pem_public_key(passport.public_key.encode())
            if not isinstance(public_key, rsa.RSAPublicKey):
                return False

            signature = bytes.fromhex(passport.signature)
            body = self._passport_body(passport)

            public_key.verify(
                signature,
                body,
                padding.PKCS1v15(),
                utils.Prehashed(hashes.SHA256()),
            )
            return True
        except (InvalidSignature, Exception):
            return False

    def _passport_body(self, passport: PluginPassport) -> bytes:
        data = (
            f"{passport.plugin_id}:{passport.publisher}:"
            f"{passport.version}:{passport.public_key}:"
            f"{','.join(sorted(passport.permissions))}"
        )
        return hashlib.sha256(data.encode()).digest()

    def _canonical_json(self, data: dict) -> str:
        import json

        return json.dumps(data, sort_keys=True, separators=(",", ":"))
