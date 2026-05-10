"""Multi-domain real-time anomaly detection for SimHPC runtime."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AnomalyEvent:
    anomaly_type: str
    severity: float
    entity_id: str
    description: str
    confidence: float
    algorithm: str = "rule_based"
    recommended_action: str = "monitor"
    metadata: dict[str, Any] = field(default_factory=dict)


class MLAnomalyDetector:
    def __init__(self) -> None:
        self._models: dict[str, Any] | None = None
        self._temporal_window = 12

    async def _ensure_models(self) -> None:
        if self._models is not None:
            return
        try:
            from backend.core.hardware.ml_integration import get_hardware_ml_models

            models = await get_hardware_ml_models().detect_anomalies([])
            self._models = {"baseline": models}
        except Exception:
            self._models = {}

    def _extract_features(self, data: list[dict[str, Any]]) -> list[list[float]]:
        features: list[list[float]] = []
        for node in data:
            features.append(
                [
                    node.get("gpu_utilization", 50),
                    node.get("gpu_temp_c", 50),
                    node.get("memory_usage_pct", 50),
                    node.get("gpu_count", 1),
                    node.get("utilization_pct", 50),
                ]
            )
        return features

    async def detect(
        self,
        telemetry: list[dict[str, Any]],
        context: dict[str, Any] | None = None,
    ) -> list[AnomalyEvent]:
        await self._ensure_models()
        candidates: list[AnomalyEvent] = []

        iso_anomalies = await self._run_isolation_forest(telemetry)
        candidates.extend(iso_anomalies)

        ae_anomalies = await self._run_autoencoder(telemetry)
        candidates.extend(ae_anomalies)

        lstm_anomalies = await self._run_lstm_temporal(telemetry)
        candidates.extend(lstm_anomalies)

        return self._ensemble_vote(candidates)

    async def _run_isolation_forest(self, data: list[dict[str, Any]]) -> list[AnomalyEvent]:
        anomalies: list[AnomalyEvent] = []
        features = self._extract_features(data)

        try:
            import numpy as np

            if len(features) < 2 or not features:
                return anomalies

            arr = np.array(features)
            mean_vals = np.mean(arr, axis=0)
            std_vals = np.std(arr, axis=0)
            std_vals = np.where(std_vals == 0, 1.0, std_vals)
            scores = np.max(np.abs((arr - mean_vals) / std_vals), axis=1)

            for i, score in enumerate(scores):
                if score > 0.45:
                    anomalies.append(
                        AnomalyEvent(
                            anomaly_type="isolation_forest",
                            severity=float(min(1.0, score)),
                            entity_id=data[i].get("node_id", f"node_{i}"),
                            description="Isolation Forest outlier detected",
                            confidence=float(min(0.95, score * 1.8)),
                            algorithm="isolation_forest",
                            recommended_action="investigate_node",
                            metadata={"isolation_score": float(score)},
                        )
                    )
        except Exception as e:
            logger.warning(f"Isolation Forest skipped: {e}")

        return anomalies

    async def _run_autoencoder(self, data: list[dict[str, Any]]) -> list[AnomalyEvent]:
        anomalies: list[AnomalyEvent] = []
        features = self._extract_features(data)

        try:
            import numpy as np

            if len(features) < 2:
                return anomalies

            arr = np.array(features)
            mean_vals = np.mean(arr, axis=0)
            mse = np.mean((arr - mean_vals) ** 2, axis=1)
            threshold = np.percentile(mse, 95) if len(mse) > 0 else 1.0

            for i, error in enumerate(mse):
                if threshold > 0 and error > threshold * 1.5:
                    anomalies.append(
                        AnomalyEvent(
                            anomaly_type="reconstruction_error",
                            severity=float(min(1.0, error / threshold)),
                            entity_id=data[i].get("node_id", f"node_{i}"),
                            description="High reconstruction error (Autoencoder)",
                            confidence=float(min(0.92, error / threshold)),
                            algorithm="autoencoder",
                            recommended_action="check_hardware_health",
                            metadata={"mse": float(error)},
                        )
                    )
        except Exception as e:
            logger.warning(f"Autoencoder detection skipped: {e}")

        return anomalies

    async def _run_lstm_temporal(self, data: list[dict[str, Any]]) -> list[AnomalyEvent]:
        anomalies: list[AnomalyEvent] = []
        if len(data) < self._temporal_window:
            return anomalies

        features = self._extract_features(data)

        try:
            import numpy as np

            arr = np.array(features)
            window = self._temporal_window
            seqs = [arr[i : i + window] for i in range(len(arr) - window + 1)]
            if not seqs:
                return anomalies

            stacked = np.stack(seqs)
            predictions = np.roll(stacked, 1, axis=0)
            predictions[0] = stacked[0]
            errors = np.abs(stacked - predictions).mean(axis=tuple(range(1, stacked.ndim)))

            for i, error in enumerate(errors):
                if error > 0.65:
                    anomalies.append(
                        AnomalyEvent(
                            anomaly_type="temporal_deviation",
                            severity=float(min(1.0, error)),
                            entity_id=data[window - 1 + i].get("node_id", f"node_{i}"),
                            description="Temporal pattern break detected (LSTM)",
                            confidence=float(min(1.0, error)),
                            algorithm="lstm_temporal",
                            recommended_action="review_regime_shift",
                            metadata={"error": float(error)},
                        )
                    )
        except Exception as e:
            logger.warning(f"LSTM temporal detection skipped: {e}")

        return anomalies

    def _ensemble_vote(self, candidates: list[AnomalyEvent]) -> list[AnomalyEvent]:
        if not candidates:
            return []

        grouped: dict[tuple[str, str], list[AnomalyEvent]] = {}
        for a in candidates:
            key = (a.entity_id, a.anomaly_type)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(a)

        final: list[AnomalyEvent] = []
        for group in grouped.values():
            avg_severity = sum(x.severity for x in group) / len(group)
            avg_conf = sum(x.confidence for x in group) / len(group)

            if avg_severity > 0.6:
                representative = group[0]
                representative.severity = avg_severity
                representative.confidence = avg_conf
                final.append(representative)

        return final


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

        try:
            from backend.core.runtime.state_registry.service import StateRegistryService

            state = await StateRegistryService.registry().get_current()
            context = {"regime": getattr(state, "regime", "normal")}
        except Exception:
            context = {"regime": "normal"}

        ml_detector = MLAnomalyDetector()
        ml_anomalies = await ml_detector.detect(node_telemetry or [], context=context)
        anomalies.extend(ml_anomalies)

        anomalies.extend(await self.detect_scheduling_anomalies(recent_requests))

        anomalies.extend(await self.detect_economic_anomalies(recent_scores))

        for anomaly in [a for a in anomalies if a.severity > 0.55]:
            try:
                from backend.core.runtime.alerting.engine import RealTimeAlertingSystem

                await RealTimeAlertingSystem.alerts().trigger(anomaly)
            except Exception:
                pass

        return anomalies


def get_anomaly_detector() -> AnomalyDetectionSystem:
    return AnomalyDetectionSystem.detector()
