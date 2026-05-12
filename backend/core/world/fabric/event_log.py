from uuid import uuid4

from pydantic import BaseModel, Field


class WorldEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: uuid4().hex)
    event_type: str
    tenant_id: str
    plugin_name: str
    timestamp: float
    payload: dict
    vector_clock: dict[str, int]
    causality_parent: str | None = None
