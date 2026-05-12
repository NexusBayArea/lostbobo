from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProtocolResponse(BaseModel):
    success: bool
    payload: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
