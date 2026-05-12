from __future__ import annotations

from pydantic import BaseModel


class ReplayMetadata(BaseModel):
    replay_hash: str
    scheduler_version: str = "1.0"
    kernel_version: str = "1.0"
    plugin_versions: dict[str, str] = {}
    deterministic_seed: int = 42
    created_at: float = 0.0
