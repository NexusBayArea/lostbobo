from datetime import datetime

from pydantic import BaseModel, Field


class ReasoningTrace(BaseModel):
    """Structured intermediate cognition for audit + tournament evaluation."""

    step: int
    thought: str
    evidence: list[str]
    confidence: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
