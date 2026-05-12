import hashlib
import json


class ExecutionHasher:
    @staticmethod
    def hash_execution(payload: dict) -> str:
        """Produce a deterministic SHA-256 hash of a JSON-serialisable dict."""
        canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
