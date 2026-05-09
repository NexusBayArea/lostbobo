"""Entity graph primitives — nodes and edges for world-state relationships."""

from __future__ import annotations

import time

from pydantic import BaseModel, Field


class EntityNode(BaseModel):
    entity_id: str
    entity_type: str
    name: str
    state_key: str
    embedding: list[float] | None = None


class RelationshipEdge(BaseModel):
    source_id: str
    target_id: str
    relation: str
    weight: float = 1.0
    last_updated: float = Field(default_factory=time.time)
    evidence_event_ids: list[str] = Field(default_factory=list)
