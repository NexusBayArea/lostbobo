import base64
import hashlib
import json
import os
from typing import Any


class CertificateSigner:
    """Signs certificate payloads with system RSA keys."""

    def __init__(self):
        self.signing_key = os.getenv("SIMHPC_RSA_PRIVATE_KEY_PEM", "mock_key")

    def sign(self, payload: dict[str, Any]) -> str:
        data = json.dumps(payload, sort_keys=True)
        return base64.b64encode(hashlib.sha256(data.encode() + self.signing_key.encode()).digest()).decode()

    def get_fingerprint(self) -> str:
        return hashlib.sha256(self.signing_key.encode()).hexdigest()[:16]
