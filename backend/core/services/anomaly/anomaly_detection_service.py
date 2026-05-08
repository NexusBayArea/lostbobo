from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np
import structlog

from backend.core.supabase_job_store import SupabaseJobStore
from backend.kernel.kernel import Kernel

log = structlog.get_logger(__name__)


@dataclass
class AnomalyResult:
    detected: bool
    anomaly_type: str
    severity: str  # LOW | MEDIUM | HIGH | CRITICAL
    score: float
    reason: str
    recommended_action: str


class AnomalyDetectionService:
    """Kernel-centered anomaly detection for runtime stability."""

    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.supabase = SupabaseJobStore()
        self.metric_windows: dict[str, list[float]] = {}

    async def detect(self, payload: dict[str, Any]) -> AnomalyResult:
        """Main anomaly detection entrypoint."""
        job_id = payload.get("job_id")
        anomaly_type = payload.get("type", "general")
        metrics = payload.get("metrics", {})

        score = 0.0
        reasons = []

        if "trust_score" in metrics:
            trust = metrics["trust_score"]
            if trust < 0.3:
                score += 0.4
                reasons.append("severe_trust_collapse")

        if "novelty_score" in metrics:
            novelty = metrics["novelty_score"]
            if novelty < 0.25:
                score += 0.35
                reasons.append("novelty_collapse")

        if "latency" in metrics:
            latency = metrics["latency"]
            window = self.metric_windows.setdefault("latency", [])
            window.append(latency)
            if len(window) > 50:
                window.pop(0)

            if len(window) > 10:
                mean = np.mean(window)
                std = np.std(window)
                if std > 0 and (latency - mean) / std > 3.0:
                    score += 0.3
                    reasons.append("latency_anomaly")

        if payload.get("loop_detected") or payload.get("safety_halt"):
            score += 0.5
            reasons.append("loop_or_safety_violation")

        final_score = min(1.0, score)
        if final_score > 0.7:
            severity = "CRITICAL"
        elif final_score > 0.45:
            severity = "HIGH"
        elif final_score > 0.2:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        result = AnomalyResult(
            detected=final_score > 0.2,
            anomaly_type=anomaly_type,
            severity=severity,
            score=round(final_score, 3),
            reason="; ".join(reasons) if reasons else "normal",
            recommended_action="HALT" if severity == "CRITICAL" else "WARN",
        )

        if result.detected:
            await self.supabase.record_event(
                "anomaly_detected",
                {
                    "job_id": job_id,
                    "anomaly_type": anomaly_type,
                    "severity": severity,
                    "score": result.score,
                    "reason": result.reason,
                    "timestamp": datetime.now().isoformat(),
                },
            )
            log.warning("anomaly detected", **result.__dict__)

        return result
