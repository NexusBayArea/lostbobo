"""Drift Detection & Safeguards — production safety layer."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Any, List

from app.kernel.kernel import Kernel

log = logging.getLogger(__name__)


@dataclass
class DriftAlert:
    type: str
    severity: str          # low | medium | high | critical
    message: str
    metric: str
    current: float
    baseline: float
    timestamp: datetime


class DriftDetector:
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.baselines: Dict[str, float] = {}
        self.history: Dict[str, List[float]] = {}
        self.quarantine = False

    async def check(self, metric_name: str, current_value: float, window: int = 20) -> DriftAlert | None:
        """Detect regression / drift."""
        if metric_name not in self.history:
            self.history[metric_name] = []

        self.history[metric_name].append(current_value)
        if len(self.history[metric_name]) > window:
            self.history[metric_name].pop(0)

        recent = self.history[metric_name][-window:]
        baseline = self.baselines.get(metric_name, sum(recent) / len(recent) if recent else current_value)

        # Simple statistical drift detection
        mean = sum(recent) / len(recent)
        degradation = (baseline - mean) / (abs(baseline) + 1e-8)

        if degradation > 0.15:   # >15% regression
            alert = DriftAlert(
                type="performance_drift",
                severity="high" if degradation > 0.3 else "medium",
                message=f"Performance drift detected on {metric_name}",
                metric=metric_name,
                current=mean,
                baseline=baseline,
                timestamp=datetime.utcnow()
            )
            await self._handle_alert(alert)
            return alert

        # Update baseline if stable
        if abs(degradation) < 0.05:
            self.baselines[metric_name] = mean

        return None

    async def _handle_alert(self, alert: DriftAlert):
        log.warning(f"🚨 DRIFT ALERT: {alert.message} | severity={alert.severity}")

        if alert.severity == "high" or alert.severity == "critical":
            self.quarantine = True
            await self.kernel.execute({
                "type": "MEMORY_RECORD",
                "payload": {
                    "type": "safeguard",
                    "content": {"alert": alert.__dict__, "action": "quarantine_activated"}
                }
            })
            # Trigger rollback in next phase
            log.error("Quarantine activated — system paused for review")

    async def reset_quarantine(self):
        self.quarantine = False
        log.info("Quarantine lifted")