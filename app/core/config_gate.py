import os
from typing import List

REQUIRED_VARS = [
    "SB_URL",
    "SB_TOKEN",
    "SB_SECRET_KEY",
    "SB_JWT_SECRET",
    "SB_PUB_KEY",
    "SB_DATA_URL",
]


def validate_raw_env() -> None:
    """Hard pre‑flight check BEFORE any app imports or Pydantic initialization.
    Ensures CI fails early with clear error messages.
    """
    missing: List[str] = []
    for key in REQUIRED_VARS:
        if not os.getenv(key):
            missing.append(key)
    if missing:
        raise RuntimeError(
            "\n❌ CONFIG GATE FAILED\n"
            + "Missing environment variables:\n"
            + "\n".join(f"  - {k}" for k in missing)
            + "\n\nFix CI or secrets configuration before proceeding."
        )
