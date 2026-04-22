import json

from runtime.contract import CONTRACT

STATE_FILE = CONTRACT.root / ".runtime_state.json"


def load_state():
    if not STATE_FILE.exists():
        return {}
    return json.loads(STATE_FILE.read_text())


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))
