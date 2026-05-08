from typing import Any

import structlog
from prometheus_client import Counter, Gauge, Histogram, Info

from backend.core.supabase_job_store import SupabaseJobStore
from backend.kernel.kernel import Kernel

log = structlog.get_logger(__name__)


class ObservabilityService:
    """Unified Observability: OTEL (Traces/Logs) + Prometheus Metrics."""

    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.supabase = SupabaseJobStore()

        # === Prometheus Metrics ===
        self.requests_total = Counter(
            "simhpc_requests_total", "Total requests", ["method", "route", "status", "tenant_id"]
        )
        self.request_duration = Histogram("simhpc_request_duration_seconds", "Request latency", ["route", "tenant_id"])
        self.trust_verifications = Counter(
            "simhpc_trust_verifications_total", "Trust verifications", ["decision", "tenant_id"]
        )
        self.novelty_score = Gauge("simhpc_novelty_score", "Composite novelty score")
        self.safety_halts = Counter("simhpc_safety_halts_total", "Safety layer halts")
        self.rl_rewards = Histogram("simhpc_rl_reward", "RL step rewards")
        self.anomaly_detected = Counter("simhpc_anomaly_detected_total", "Anomalies", ["type", "severity"])

        self.build_info = Info("simhpc_build_info", "Build info")
        self.build_info.info({"version": "0.5.0", "kernel": "true"})

    async def record_request(self, payload: dict[str, Any]):
        self.requests_total.labels(
            method=payload["method"],
            route=payload["route"],
            status=payload["status"],
            tenant_id=payload.get("tenant_id", "unknown"),
        ).inc()
        self.request_duration.labels(route=payload["route"], tenant_id=payload.get("tenant_id", "unknown")).observe(
            payload["duration"]
        )

    def record_trust_verification(self, decision: str, score: float, tenant_id: str):
        self.trust_verifications.labels(decision=decision, tenant_id=tenant_id).inc()
        self.novelty_score.set(score)

    def record_safety_halt(self):
        self.safety_halts.inc()

    def record_rl_reward(self, reward: float):
        self.rl_rewards.observe(reward)

    def record_anomaly(self, anomaly_type: str, severity: str):
        self.anomaly_detected.labels(type=anomaly_type, severity=severity).inc()
