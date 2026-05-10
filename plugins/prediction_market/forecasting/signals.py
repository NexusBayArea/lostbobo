"""Core signal model for prediction market ingestion."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class ForecastSignal(BaseModel):
    id: str
    source: str
    signal_type: str
    market_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    value: float
    confidence: float
    metadata: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)


class MarketQuestion(BaseModel):
    question_id: str
    question_text: str
    market_source: str
    resolved: bool = False
    outcome: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class IngestedBatch(BaseModel):
    batch_id: str
    signals: list[ForecastSignal]
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_count: int = 0

    @property
    def source_count_prop(self) -> int:
        return len(set(s.source for s in self.signals))
