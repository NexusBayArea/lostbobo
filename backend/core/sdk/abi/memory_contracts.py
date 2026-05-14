from __future__ import annotations

from pydantic import BaseModel, Field


class MemoryAccessPolicy(BaseModel):
    tier: str
    namespace: str
    read_allowed: bool = False
    write_allowed: bool = False
    evict_allowed: bool = False
    ttl_seconds: int | None = None
    confidence_threshold: float | None = Field(default=None, ge=0.0, le=1.0)


class MemoryFabricAccess(BaseModel):
    policies: list[MemoryAccessPolicy] = Field(default_factory=list)
    default_ttl_seconds: int | None = None
    max_namespaces: int = 10


class MemoryKey(BaseModel):
    namespace: str
    key: str
    tier: str = "episodic"


class MemoryEntry(BaseModel):
    key: MemoryKey
    value: bytes
    ttl_seconds: int | None = None
    plugin_source: str = ""
