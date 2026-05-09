from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from backend.core.probability.prediction import Prediction


class ForecastRequest(BaseModel):
    topic: str
    horizon: datetime | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class ForecastResponse(BaseModel):
    prediction: Prediction
    reasoning: dict[str, Any]  # structured reasoning trace
    confidence_sources: list[str]
