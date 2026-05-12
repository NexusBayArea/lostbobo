from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    EXECUTION = "execution"
    CAUSAL = "causal"
    WORKING = "working"


class MemoryScope(str, Enum):
    TENANT = "tenant"
    PLUGIN = "plugin"
    GLOBAL = "global"


class MemoryImportance(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BaseMemoryRecord(BaseModel):
    memory_id: str = Field(default_factory=lambda: uuid4().hex)
    tenant_id: str
    plugin_name: str
    memory_type: MemoryType
    scope: MemoryScope = MemoryScope.TENANT
    timestamp: float
    confidence: float = 1.0
    ttl_seconds: int | None = None
    importance: MemoryImportance = MemoryImportance.MEDIUM
    lineage_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None


class MemoryQuota(BaseModel):
    max_records: int = 100000
    max_bytes: int = 1024 * 1024 * 100
