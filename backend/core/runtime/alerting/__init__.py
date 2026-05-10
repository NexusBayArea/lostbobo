"""Real-time Alerting System — operational nervous system."""

from __future__ import annotations

from backend.core.runtime.alerting.engine import (
    Alert,
    AlertFatigueGuard,
    RealTimeAlertingSystem,
    get_alerting_system,
)

__all__ = [
    "Alert",
    "AlertFatigueGuard",
    "RealTimeAlertingSystem",
    "get_alerting_system",
]
