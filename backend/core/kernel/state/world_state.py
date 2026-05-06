"""WorldState — probabilistic digital twin (Kernel-owned)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Uncertainty:
    mean: float = 0.0
    std: float | None = None
    distribution: str = "normal"
    bounds: list[float] | None = None


@dataclass
class EntityVariable:
    value: float = 0.0
    uncertainty: Uncertainty = field(default_factory=lambda: Uncertainty(mean=0.0))
    unit: str | None = None


@dataclass
class WorldState:
    state_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    entities: dict[str, dict[str, EntityVariable]] = field(default_factory=dict)
    relations: list[tuple[str, str, str]] = field(default_factory=list)
    scenarios: dict[str, dict[str, Any]] = field(default_factory=dict)
    tenant_id: str = "public"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.state_id:
            self.state_id = f"world_{int(datetime.utcnow().timestamp()*1000)}"
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

    def snapshot(self) -> dict[str, Any]:
        """Return serializable snapshot for agents/skills."""
        entities_serialized = {}
        for entity, vars_dict in self.entities.items():
            entities_serialized[entity] = {}
            for var_name, var in vars_dict.items():
                entities_serialized[entity][var_name] = {
                    "value": var.value,
                    "uncertainty": {"mean": var.uncertainty.mean, "std": var.uncertainty.std},
                    "unit": var.unit,
                }

        return {
            "state_id": self.state_id,
            "timestamp": self.timestamp.isoformat(),
            "entities": entities_serialized,
            "relations": self.relations,
            "scenarios": self.scenarios,
        }

    def apply_update(self, update: dict[str, Any]):
        """Apply delta update with uncertainty."""
        entity = update.get("entity")
        var_name = update.get("variable")
        value = update.get("value")
        uncertainty = update.get("uncertainty")

        if entity not in self.entities:
            self.entities[entity] = {}

        unc = Uncertainty(**uncertainty) if isinstance(uncertainty, dict) else uncertainty
        self.entities[entity][var_name] = EntityVariable(
            value=value,
            uncertainty=unc,
            unit=update.get("unit"),
        )

        if "relations" in update:
            self.relations.extend(update["relations"])

        if "scenario" in update:
            self.scenarios[update["scenario"]] = update.get("data", {})
