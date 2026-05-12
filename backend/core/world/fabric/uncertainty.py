from pydantic import BaseModel


class UncertaintyEnvelope(BaseModel):
    confidence: float = 1.0
    entropy: float = 0.0
    variance: float = 0.0
    provenance_weight: float = 1.0
