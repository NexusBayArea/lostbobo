"""
Unified Observability Service (Singleton + Kernel-Centered)
Supports Prometheus metrics, structured logging, and OpenTelemetry.
"""

import logging
from dataclasses import dataclass
from typing import Any

from prometheus_client import Counter, Gauge, Histogram, Info

from backend.core.services.tracing import tracer

logger = logging.getLogger(__name__)


@dataclass
class MetricLabels:
    tenant_id: str | None = None
    domain: str | None = None
    model_version: str | None = None


class ObservabilityService:
    """
    Singleton observability service used across the entire platform.
    """

    _instance: "ObservabilityService | None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self._metrics: dict[str, Any] = {}

        self._metrics["simulations_started_total"] = Counter(
            "simulations_started_total", "Total simulations started", ["tenant_id"]
        )
        self._metrics["simulations_completed_total"] = Counter(
            "simulations_completed_total", "Total simulations completed", ["tenant_id"]
        )
        self._metrics["simulations_failed_total"] = Counter(
            "simulations_failed_total", "Total simulations failed", ["tenant_id"]
        )
        self._metrics["flywheel_runs_ingested_total"] = Counter(
            "flywheel_runs_ingested_total", "Runs ingested into Flywheel", ["domain"]
        )
        self._metrics["flywheel_prior_confidence_avg"] = Gauge(
            "flywheel_prior_confidence_avg", "Average prior confidence"
        )
        self._metrics["ml_training_started_total"] = Counter("ml_training_started_total", "ML training jobs started")
        self._metrics["ml_inference_total"] = Counter(
            "ml_inference_total", "Physics inference calls", ["model_used", "task_type"]
        )
        self._metrics["ml_inference_latency_ms"] = Histogram(
            "ml_inference_latency_ms", "Inference latency (ms)", ["model_used"]
        )
        self._metrics["audit_log_entries_total"] = Counter(
            "audit_log_entries_total", "Audit log entries written", ["event_type"]
        )
        self._metrics["compliance_rollbacks_total"] = Counter("compliance_rollbacks_total", "Automatic model rollbacks")
        self._metrics["simhpc_requests_total"] = Counter(
            "simhpc_requests_total", "Total requests", ["method", "route", "status", "tenant_id"]
        )
        self._metrics["simhpc_request_duration_seconds"] = Histogram(
            "simhpc_request_duration_seconds", "Request latency", ["route", "tenant_id"]
        )
        self._metrics["simhpc_trust_verifications_total"] = Counter(
            "simhpc_trust_verifications_total", "Trust verifications", ["decision", "tenant_id"]
        )
        self._metrics["simhpc_novelty_score"] = Gauge("simhpc_novelty_score", "Composite novelty score")
        self._metrics["simhpc_safety_halts_total"] = Counter("simhpc_safety_halts_total", "Safety layer halts")
        self._metrics["simhpc_rl_reward"] = Histogram("simhpc_rl_reward", "RL step rewards")
        self._metrics["simhpc_anomaly_detected_total"] = Counter(
            "simhpc_anomaly_detected_total", "Anomalies", ["type", "severity"]
        )
        self._metrics["anomaly_scans_total"] = Counter("anomaly_scans_total", "Total anomaly scans run")
        self._metrics["anomaly_isolation_forest_detected"] = Counter(
            "anomaly_isolation_forest_detected", "Isolation Forest anomalies", ["node_id"]
        )
        self._metrics["anomaly_autoencoder_mse"] = Counter(
            "anomaly_autoencoder_mse", "Autoencoder anomalies", ["node_id"]
        )
        self._metrics["anomaly_lstm_temporal"] = Counter(
            "anomaly_lstm_temporal", "LSTM temporal anomalies", ["node_id"]
        )
        self._metrics["ensemble_anomalies_total"] = Counter("ensemble_anomalies_total", "Total ensemble anomalies")
        self._metrics["alerts_triggered_total"] = Counter("alerts_triggered_total", "Alerts triggered", ["severity"])
        self._metrics["active_alerts"] = Gauge("active_alerts", "Currently active alerts")

        self._metrics["build_info"] = Info("simhpc_build_info", "Build info")
        self._metrics["build_info"].info({"version": "0.5.0", "kernel": "true"})

        logger.info("✅ ObservabilityService initialized (Prometheus metrics ready)")

    def increment(self, metric_name: str, labels: dict[str, str] | None = None, value: int = 1):
        if metric_name not in self._metrics:
            logger.warning(f"Unknown metric: {metric_name}")
            return
        metric = self._metrics[metric_name]
        if isinstance(metric, Counter):
            if labels:
                metric.labels(**labels).inc(value)
            else:
                metric.inc(value)
        else:
            logger.warning(f"Cannot increment non-counter metric: {metric_name}")

    def gauge(self, metric_name: str, value: float, labels: dict[str, str] | None = None):
        if metric_name not in self._metrics:
            return
        metric = self._metrics[metric_name]
        if isinstance(metric, Gauge):
            if labels:
                metric.labels(**labels).set(value)
            else:
                metric.set(value)

    def observe(self, metric_name: str, value: float, labels: dict[str, str] | None = None):
        if metric_name not in self._metrics:
            return
        metric = self._metrics[metric_name]
        if isinstance(metric, Histogram):
            if labels:
                metric.labels(**labels).observe(value)
            else:
                metric.observe(value)

    def info(self, metric_name: str, labels: dict[str, str]):
        if metric_name in self._metrics and isinstance(self._metrics[metric_name], Info):
            self._metrics[metric_name].info(labels)

    def start_span(self, name: str, attributes: dict[str, Any] | None = None):
        """Start a traced OpenTelemetry span."""
        return tracer.start_as_current_span(name, attributes=attributes or {})

    async def record_request(self, payload: dict[str, Any]):
        self.increment(
            "simhpc_requests_total",
            {
                "method": payload["method"],
                "route": payload["route"],
                "status": payload["status"],
                "tenant_id": payload.get("tenant_id", "unknown"),
            },
        )
        self.observe(
            "simhpc_request_duration_seconds",
            payload["duration"],
            {
                "route": payload["route"],
                "tenant_id": payload.get("tenant_id", "unknown"),
            },
        )

    def record_trust_verification(self, decision: str, score: float, tenant_id: str):
        self.increment("simhpc_trust_verifications_total", {"decision": decision, "tenant_id": tenant_id})
        self.gauge("simhpc_novelty_score", score)

    def record_safety_halt(self):
        self.increment("simhpc_safety_halts_total")

    def record_rl_reward(self, reward: float):
        self.observe("simhpc_rl_reward", reward)

    def record_anomaly(self, anomaly_type: str, severity: str):
        self.increment("simhpc_anomaly_detected_total", {"type": anomaly_type, "severity": severity})


_observability: ObservabilityService | None = None


def observability() -> ObservabilityService:
    global _observability
    if _observability is None:
        _observability = ObservabilityService()
    return _observability
