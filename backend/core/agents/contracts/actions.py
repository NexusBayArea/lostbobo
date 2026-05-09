from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from backend.core.probability.prediction import Prediction


class Action(BaseModel):
    """Standardized output from agents."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_id: str
    action_type: str  # "forecast", "mutate_state", "request_info", ...
    payload: Dict[str, Any]
    confidence: float = 1.0
    predicted_impact: Optional[Prediction] = None  # from probability layer
