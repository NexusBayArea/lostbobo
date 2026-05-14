from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ForecastResult:
    mean: float
    distribution: Any = None
    confidence_interval: tuple[float, float] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ProbabilisticForecastModel(ABC):
    @abstractmethod
    async def predict(self, payload: dict[str, Any]) -> ForecastResult: ...


class ProbabilisticForecast:
    def __init__(self, model: ProbabilisticForecastModel):
        self.model = model

    async def run(self, payload: dict[str, Any]) -> ForecastResult:
        return await self.model.predict(payload)
