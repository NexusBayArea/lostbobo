from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class OnboardingBase(BaseModel):
    current_step: str
    completed_steps: List[str] = []
    events: List[str] = []
    skipped: bool = False

class OnboardingResponse(OnboardingBase):
    version: int
    updated_at: datetime

class OnboardingUpdate(OnboardingBase):
    version: int

class EventRequest(BaseModel):
    event: str
