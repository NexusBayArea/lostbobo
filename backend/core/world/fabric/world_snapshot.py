from pydantic import BaseModel, Field

from backend.core.world.fabric.uncertainty import UncertaintyEnvelope


class WorldSnapshot(BaseModel):
    snapshot_id: str
    tenant_id: str
    timestamp: float
    branch_id: str
    parent_snapshot_id: str | None = None
    state: dict = Field(default_factory=dict)
    uncertainty: dict[str, UncertaintyEnvelope] = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)
