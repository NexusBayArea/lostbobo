"""WorldState — probabilistic digital twin with explicit uncertainty."""

from __future__ import annotations

import time
import uuid
from typing import Any

from pydantic import BaseModel, Field


class EntityVariable(BaseModel):
    value: Any
    uncertainty: float = Field(default=0.0, ge=0.0, le=1.0)
    half_life_s: float = Field(default=3600 * 24)
    last_updated: float = Field(default_factory=time.time)
    provenance_event_id: str = ""


class UncertaintyField(BaseModel):
    mean: float
    std: float = 0.0
    source_reliability: float = 1.0
    contributing_events: list[str] = Field(default_factory=list)


class WorldState(BaseModel):
    state_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    causal_id: str = "genesis"
    regime: str = "normal"

    entities: dict[str, EntityVariable] = Field(default_factory=dict)
    uncertainty: dict[str, UncertaintyField] = Field(default_factory=dict)
    provenance: dict[str, str] = Field(default_factory=dict)
    pending_events: list[str] = Field(default_factory=list)

    def apply_event(self, event: SimHPCEvent) -> WorldState:  # noqa: F821
        new_state = self.model_copy(deep=True)
        new_state.timestamp = event.timestamp
        new_state.causal_id = event.causal_id
        new_state.provenance[f"event:{event.event_id}"] = event.provenance_hash or ""

        payload = event.payload or {}
        for key, val in payload.items():
            if key.startswith("entity:"):
                entity_key = key[7:]
                new_state.entities[entity_key] = EntityVariable(
                    value=val.get("value"),
                    uncertainty=val.get("uncertainty", 0.0),
                    provenance_event_id=event.event_id,
                )
            elif key.startswith("uncertainty:"):
                unc_key = key[12:]
                new_state.uncertainty[unc_key] = UncertaintyField(
                    mean=val.get("mean", 0.0),
                    std=val.get("std", 0.0),
                    contributing_events=[event.event_id],
                )

        if "regime" in payload:
            new_state.regime = payload["regime"]

        return new_state
