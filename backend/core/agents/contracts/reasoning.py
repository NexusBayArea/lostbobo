from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class ReasoningTrace(BaseModel):
    """Structured intermediate cognition for audit + tournament evaluation."""
    step: int
    thought: str
    evidence: List[str]
    confidence: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
