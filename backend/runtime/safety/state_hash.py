import hashlib
import json
from typing import Any


class StateHasher:
    def hash(self, state: dict[str, Any]) -> str:
        serialized = json.dumps(state, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()
