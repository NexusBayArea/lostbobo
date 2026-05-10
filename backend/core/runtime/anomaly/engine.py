"""Multi-domain real-time anomaly detection for SimHPC runtime."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AnomalyEvent:
    anomaly_type: str
    severity: float
    entity_id: str
    description: str
    confidence: float
    recommended_action: str
    metadata: dict[str, Any]


class AnomalyDetectionSystem:
    _instance: AnomalyDetectionSystem | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._recent_margins: list[float] = []
        self._recent_scheduling: list[dict[str, Any]] = []

    @classmethod
    def detector(cls) -> AnomalyDetectionSystem:
        return cls()

    async def detect_hardware_anomalies(self, node_telemetry: list[dict[str, Any]]) -> list[AnomalyEvent]:
        self._ensure_initialized()
        anomalies: list[AnomalyEvent] = []
        try:
            from backend.core.hardware.ml_integration import get_hardware_ml_models

            ml = get_hardware_ml_models()
            results = await ml.detect_anomalies(node_telemetry)
            for r in results:
                if r.get("anomaly_score", 0) > 0.75:
                    anomalies.append(
                        AnomalyEvent(
                            anomaly_type="hardware_node",
                            severity=r["anomaly_score"],
                            entity_id=r.get("node_id", "unknown"),
                            description=r.get("reason", "unknown"),
                            confidence=r["anomaly_score"],
                            recommended_action="drain_and_replace" if r["anomaly_score"] > 0.9 else "monitor",
                            metadata=r,
                        )
                    )
        except Exception as e:
            logger.warning(f"Hardware anomaly detection skipped: {e}")
        return anomalies

    async def detect_scheduling_anomalies(
        self, recent_requests: list[dict[str, Any]] | None = None
    ) -> list[AnomalyEvent]:
        self._ensure_initialized()
        if recent_requests is None:
            recent_requests = self._recent_scheduling
        if len(recent_requests) < 5:
            return []

        isolated_ratio = sum(1 for r in recent_requests if r.get("sla_tier") == "defense") / len(recent_requests)

        if isolated_ratio > 0.4:
            return [
                AnomalyEvent(
                    anomaly_type="scheduling_spike",
                    severity=0.82,
                    entity_id="global_scheduler",
                    description="Unusual surge in isolated/defense requests",
                    confidence=0.78,
                    recommended_action="increase_isolated_reserve",
                    metadata={"isolated_ratio": isolated_ratio},
                )
            ]
        return []

    async def detect_economic_anomalies(self, recent_scores: list[float] | None = None) -> list[AnomalyEvent]:
        self._ensure_initialized()
        if recent_scores is None:
            recent_scores = self._recent_margins
        if not recent_scores:
            return []

        try:
            import numpy

            mean_margin = float(numpy.mean(recent_scores))
            std_margin = float(numpy.std(recent_scores)) if len(recent_scores) > 1 else 0.0
        except Exception:
            mean_margin = sum(recent_scores) / len(recent_scores)
            std_margin = 0.0

        for i, score in enumerate(recent_scores):
            if abs(score - mean_margin) > 2.5 * std_margin and score < 0.1:
                return [
                    AnomalyEvent(
                        anomaly_type="economic_outlier",
                        severity=0.75,
                        entity_id=f"allocation_{i}",
                        description="Unusually low margin allocation",
                        confidence=0.71,
                        recommended_action="review_pricing",
                        metadata={"margin": score},
                    )
                ]
        return []

    def record_margin(self, margin: float) -> None:
        self._ensure_initialized()
        self._recent_margins.append(margin)
        if len(self._recent_margins) > 100:
            self._recent_margins = self._recent_margins[-100:]

    def record_scheduling_request(self, request: dict[str, Any]) -> None:
        self._ensure_initialized()
        self._recent_scheduling.append(request)
        if len(self._recent_scheduling) > 100:
            self._recent_scheduling = self._recent_scheduling[-100:]

    async def run_full_scan(
        self,
        node_telemetry: list[dict[str, Any]] | None = None,
        recent_requests: list[dict[str, Any]] | None = None,
        recent_scores: list[float] | None = None,
    ) -> list[AnomalyEvent]:
        self._ensure_initialized()
        anomalies: list[AnomalyEvent] = []

        try:
            from backend.core.services.observability_service import observability

            obs = observability()
            obs.increment("anomaly_scans_total")
        except Exception:
            pass

        if node_telemetry:
            anomalies.extend(await self.detect_hardware_anomalies(node_telemetry))

        anomalies.extend(await self.detect_scheduling_anomalies(recent_requests))

        anomalies.extend(await self.detect_economic_anomalies(recent_scores))

        for anomaly in [a for a in anomalies if a.severity > 0.7]:
            try:
                from backend.core.runtime.event_fabric.log import EventLogService
                from backend.core.runtime.event_fabric.schema import SimHPCEvent

                await EventLogService.event_log().publish(
                    SimHPCEvent(
                        event_type="anomaly.detected",
                        source_plugin="kernel",
                        confidence=anomaly.confidence,
                        payload=anomaly.__dict__,
                    )
                )
            except Exception:
                pass

        return anomalies


def get_anomaly_detector() -> AnomalyDetectionSystem:
    return AnomalyDetectionSystem.detector()
