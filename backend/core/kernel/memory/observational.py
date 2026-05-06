"""Observational Memory — events → signals → state updates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class Event:
    id: str
    type: str
    timestamp: datetime
    payload: dict[str, Any]
    source: str


@dataclass
class Observation:
    id: str
    event_ids: list[str]
    insight: str
    confidence: float
    signals: dict[str, Any]
    timestamp: datetime


class Observer:
    """Extracts structured signals from raw events."""

    def __init__(self, kernel: "Kernel"):
        self.kernel = kernel

    async def observe(self, event_data: Event | dict[str, Any]) -> Observation:
        """Turn raw event into actionable observation."""
        if isinstance(event_data, dict):
            event = Event(**event_data)
        else:
            event = event_data

        insight = f"Detected {event.type} with value {event.payload.get('value', 'N/A')}"
        confidence = 0.85 if "simulation" in event.type else 0.65

        obs = Observation(
            id=f"obs_{int(datetime.utcnow().timestamp()*1000)}",
            event_ids=[event.id],
            insight=insight,
            confidence=confidence,
            signals=event.payload,
            timestamp=datetime.utcnow(),
        )

        await self.kernel.execute({
            "type": "MEMORY_RECORD",
            "payload": {
                "type": "observation",
                "content": obs.__dict__,
            },
        })

        return obs