from __future__ import annotations

from datetime import datetime, timedelta


class TemporalWindow:
    def __init__(self, duration: timedelta):
        self.duration = duration

    def contains(self, timestamp: datetime, current: datetime) -> bool:
        return (current - timestamp) <= self.duration
