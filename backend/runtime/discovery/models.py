"""Discovery Graph Models — structured scientific discoveries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class DiscoveryNode:
    discovery_id: str
    type: str
    experiment_id: str
    swarm_id: str | None = None
    agent_id: str | None = None
    score: float
    parameters: dict[str, Any]
    metrics: dict[str, float]
    metadata: dict[str, Any] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class DiscoveryLink:
    parent_id: str
    child_id: str
    relation: str
    strength: float = 1.0
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
