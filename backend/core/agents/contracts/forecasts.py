from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.core.probability.prediction import Prediction


class ForecastRequest(BaseModel):
    topic: str
    horizon: Optional[datetime] = None
    context: Dict[str, Any] = Field(default_factory=dict)


class ForecastResponse(BaseModel):
    prediction: Prediction
    reasoning: Dict[str, Any]  # structured reasoning trace
    confidence_sources: List[str]
