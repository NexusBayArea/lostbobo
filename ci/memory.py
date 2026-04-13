import json
from pathlib import Path

STORE = Path("ci/failure_store.json")

def load_memory():
    """Loads the failure-fix memory from disk."""
    if not STORE.exists():
        return []
    try:
        return json.loads(STORE.read_text())
    except Exception:
        return []

def save_memory(data):
    """Persists the updated memory to disk."""
    STORE.write_text(json.dumps(data, indent=2))
