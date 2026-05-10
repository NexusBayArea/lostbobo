from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class CausalEdge(BaseModel):
    """Explicit causal relationship (extends DAGEdge)."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    source: str
    target: str
    causal_strength: float  # 0.0–1.0 estimated effect size
    confidence: float = 0.8
    mechanism: str = "direct"  # direct, indirect, confounding, etc.
    metadata: dict[str, Any] = Field(default_factory=dict)


class Intervention(BaseModel):
    """do(X = x) operation."""

    variable: str
    value: Any
    timestamp: float = Field(default_factory=time.time)


class CausalEffect(BaseModel):
    """Estimated causal effect."""

    treatment: str
    outcome: str
    ate: float  # Average Treatment Effect
    confidence_interval: tuple[float, float]
    method: str  # "backdoor", "frontdoor", "instrumental", ...
    provenance: list[str] = Field(default_factory=list)
