from app.core.config_gate import validate_raw_env
from app.core.env import normalize_env


def bootstrap() -> None:
    """MUST be called before ANY app import side‑effects."""
    validate_raw_env()
    normalize_env()
