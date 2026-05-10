from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from backend.core.probability.prediction import Prediction


class ForecastRecord(BaseModel):
    """Every prediction becomes a measurable scientific artifact."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_id: str
    plugin_id: str
    domain: str

    prediction: Prediction  # First-class probability object

    predicted_outcome: Any | None = None
    actual_outcome: Any | None = None
    resolved: bool = False

    calibration_delta: float | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)
    provenance_event_ids: list[str] = Field(default_factory=list)

    def is_resolved(self) -> bool:
        return self.resolved and self.actual_outcome is not None

    def brier_score(self) -> float | None:
        from .scoring import brier_score

        if not self.is_resolved():
            return None
        return brier_score(self.prediction.value, int(self.actual_outcome))
