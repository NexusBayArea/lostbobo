"""WorldState — probabilistic digital twin with explicit uncertainty."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class Uncertainty:
    mean: float
    std: float | None = None
    distribution: str = "normal"
    bounds: list[float] | None = None


@dataclass
class EntityVariable:
    value: float
    uncertainty: Uncertainty
    unit: str | None = None


@dataclass
class WorldState:
    state_id: str
    timestamp: datetime
    entities: dict[str, dict[str, EntityVariable]]
    relations: list[tuple[str, str, str]]
    scenarios: dict[str, dict[str, Any]]
    tenant_id: str
    metadata: dict[str, Any]

    def __post_init__(self):
        if not self.state_id:
            self.state_id = f"state_{int(datetime.utcnow().timestamp()*1000)}"
        if not self.timestamp:
            self.timestamp = datetime.utcnow()
        if not self.entities:
            self.entities = {}
        if not self.relations:
            self.relations = []
        if not self.scenarios:
            self.scenarios = {}
        if not self.tenant_id:
            self.tenant_id = "public"
        if not self.metadata:
            self.metadata = {}
