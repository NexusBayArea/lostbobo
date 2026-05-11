# backend/core/runtime/anomaly/detector.py
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from backend.core.runtime.entity_graph.service import EntityGraphService
from backend.core.runtime.event_fabric.log import EventLogService

log = logging.getLogger(__name__)


@dataclass
class CausalAnomaly:
    anomaly_id: str
    anomaly_type: str
    severity: str
    description: str
    affected_entity_keys: list[str] = field(default_factory=list)
    confidence: float = 0.0
    causal_id: str = ""
    timestamp: float = field(default_factory=time.time)
    evidence: dict[str, Any] = field(default_factory=dict)


class CausalAnomalyDetector:
    """Singleton causal anomaly detector."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._running = False
            cls._instance._task = None
            cls._instance._recent_anomalies: list[CausalAnomaly] = []
        return cls._instance

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._detection_loop())
        log.info("CausalAnomalyDetector started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _detection_loop(self):
        while self._running:
            try:
                await self._run_detection_pass()
                await asyncio.sleep(5)
            except Exception as e:
                log.error("Anomaly detection pass failed: %s", e)
                await asyncio.sleep(10)

    async def _run_detection_pass(self):
        """Run all causal anomaly checks."""
        try:
            state = await self._get_state_snapshot()
            graph = await EntityGraphService.graph().get_world_state_graph()

            anomalies: list[CausalAnomaly] = []

            causal_anomalies = await self._detect_causal_breaks(state, graph)
            anomalies.extend(causal_anomalies)

            regime_anomalies = await self._detect_regime_shift(state)
            anomalies.extend(regime_anomalies)

            uncertainty_anomalies = self._detect_uncertainty_spikes(state)
            anomalies.extend(uncertainty_anomalies)

            mass_anomalies = self._detect_probability_mass_violation(state)
            anomalies.extend(mass_anomalies)

            temporal_anomalies = await self._detect_temporal_monotonicity(state)
            anomalies.extend(temporal_anomalies)

            for anomaly in anomalies:
                await self._emit_anomaly(anomaly)
                self._recent_anomalies.append(anomaly)

            self._recent_anomalies = self._recent_anomalies[-100:]

            await self._run_ml_predictions()

            await self._run_rl_adaptation(state, anomalies)
        except Exception as e:
            log.error("Detection pass error: %s", e)

    async def _get_state_snapshot(self):
        try:
            from backend.core.runtime.state_registry.service import StateRegistryService

            return await StateRegistryService().get_latest_snapshot()
        except Exception:
            return {"regime": "normal", "entropy": 0.0, "causal_id": ""}

    async def _detect_causal_breaks(self, state: dict, graph: dict) -> list[CausalAnomaly]:
        anomalies: list[CausalAnomaly] = []
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        if not nodes or not edges:
            return anomalies

        try:
            causal_id = state.get("causal_id", "")
            if not causal_id or len(causal_id) < 8:
                anomalies.append(
                    CausalAnomaly(
                        anomaly_id=str(uuid4()),
                        anomaly_type="causal_break",
                        severity="medium",
                        description="Causal ID invalid or missing - possible causal graph break",
                        affected_entity_keys=[],
                        confidence=0.75,
                        causal_id=causal_id,
                        evidence={"state": state},
                    )
                )
        except Exception as e:
            log.warning("Causal break detection failed: %s", e)

        return anomalies

    async def _detect_regime_shift(self, state: dict) -> list[CausalAnomaly]:
        anomalies: list[CausalAnomaly] = []
        try:
            regime = state.get("regime", "normal")
            entropy = state.get("entropy", 0.0)

            if regime == "panic" and entropy > 0.8:
                anomalies.append(
                    CausalAnomaly(
                        anomaly_id=str(uuid4()),
                        anomaly_type="regime_shift",
                        severity="critical",
                        description="Panic regime with high entropy - system instability detected",
                        affected_entity_keys=[],
                        confidence=0.92,
                        causal_id=state.get("causal_id", ""),
                        evidence={"regime": regime, "entropy": entropy},
                    )
                )
            elif regime == "disruption" and entropy > 0.6:
                anomalies.append(
                    CausalAnomaly(
                        anomaly_id=str(uuid4()),
                        anomaly_type="regime_shift",
                        severity="high",
                        description="Disruption regime with elevated entropy",
                        affected_entity_keys=[],
                        confidence=0.78,
                        causal_id=state.get("causal_id", ""),
                        evidence={"regime": regime, "entropy": entropy},
                    )
                )
        except Exception as e:
            log.warning("Regime shift detection failed: %s", e)

        return anomalies

    def _detect_uncertainty_spikes(self, state: dict) -> list[CausalAnomaly]:
        anomalies: list[CausalAnomaly] = []
        try:
            entropy = state.get("entropy", 0.0)

            if entropy > 0.85:
                anomalies.append(
                    CausalAnomaly(
                        anomaly_id=str(uuid4()),
                        anomaly_type="uncertainty_spike",
                        severity="high",
                        description=f"Entropy spike detected: {entropy:.3f} (threshold: 0.85)",
                        affected_entity_keys=[],
                        confidence=0.88,
                        causal_id=state.get("causal_id", ""),
                        evidence={"entropy": entropy},
                    )
                )
            elif entropy > 0.7:
                anomalies.append(
                    CausalAnomaly(
                        anomaly_id=str(uuid4()),
                        anomaly_type="uncertainty_spike",
                        severity="medium",
                        description=f"Elevated entropy: {entropy:.3f}",
                        affected_entity_keys=[],
                        confidence=0.65,
                        causal_id=state.get("causal_id", ""),
                        evidence={"entropy": entropy},
                    )
                )
        except Exception as e:
            log.warning("Uncertainty spike detection failed: %s", e)

        return anomalies

    def _detect_probability_mass_violation(self, state: dict) -> list[CausalAnomaly]:
        anomalies: list[CausalAnomaly] = []
        try:
            probabilities = state.get("probabilities", {})

            total_mass = sum(probabilities.values()) if probabilities else 0.0

            if abs(total_mass - 1.0) > 0.05:
                anomalies.append(
                    CausalAnomaly(
                        anomaly_id=str(uuid4()),
                        anomaly_type="probability_mass_violation",
                        severity="high",
                        description=f"Probability mass conservation violated: {total_mass:.3f}",
                        affected_entity_keys=list(probabilities.keys())[:5],
                        confidence=0.85,
                        causal_id=state.get("causal_id", ""),
                        evidence={"total_mass": total_mass, "probabilities": probabilities},
                    )
                )
        except Exception as e:
            log.warning("Probability mass violation detection failed: %s", e)

        return anomalies

    async def _detect_temporal_monotonicity(self, state: dict) -> list[CausalAnomaly]:
        anomalies: list[CausalAnomaly] = []
        try:
            timestamp = state.get("timestamp", 0.0)
            prev_timestamp = state.get("previous_timestamp", 0.0)

            if prev_timestamp > 0 and timestamp < prev_timestamp:
                anomalies.append(
                    CausalAnomaly(
                        anomaly_id=str(uuid4()),
                        anomaly_type="temporal_monotonicity",
                        severity="critical",
                        description=f"Time went backwards: {prev_timestamp} -> {timestamp}",
                        affected_entity_keys=[],
                        confidence=0.95,
                        causal_id=state.get("causal_id", ""),
                        evidence={"prev_timestamp": prev_timestamp, "timestamp": timestamp},
                    )
                )
        except Exception as e:
            log.warning("Temporal monotonicity detection failed: %s", e)

        return anomalies

    async def _emit_anomaly(self, anomaly: CausalAnomaly):
        try:
            event_log = EventLogService()
            await event_log.publish(
                event_type="runtime.anomaly.detected",
                source_plugin="core.anomaly.detector",
                confidence=anomaly.confidence,
                payload=anomaly.__dict__,
                causal_id=anomaly.causal_id,
            )
        except Exception as e:
            log.warning("Failed to emit anomaly event: %s", e)

        log.warning(
            "Causal anomaly detected: %s (severity=%s)",
            anomaly.anomaly_type,
            anomaly.severity,
        )

        if anomaly.severity == "critical":
            await self._trigger_auto_quarantine(anomaly)

    async def _trigger_auto_quarantine(self, anomaly: CausalAnomaly):
        log.critical("Auto-quarantine triggered for anomaly: %s", anomaly.anomaly_id)

    async def get_recent_anomalies(self, limit: int = 50) -> list[dict[str, Any]]:
        return [a.__dict__ for a in self._recent_anomalies[-limit:]]

    async def _run_ml_predictions(self):
        """Run ML-based anomaly predictions."""
        try:
            from backend.core.runtime.anomaly.ml_predictor import ml_anomaly_predictor

            predictions = await ml_anomaly_predictor.predict()
            for pred in predictions:
                anomaly = CausalAnomaly(
                    anomaly_id=str(uuid4()),
                    anomaly_type=f"predicted_{pred.anomaly_type}",
                    severity=pred.severity,
                    description=f"ML-predicted {pred.anomaly_type} in {pred.horizon_seconds}s",
                    affected_entity_keys=pred.affected_entity_keys,
                    confidence=pred.probability,
                    causal_id="predicted",
                    timestamp=time.time(),
                    evidence={"ml_probability": pred.probability, **pred.features},
                )
                await self._emit_anomaly(anomaly)
                self._recent_anomalies.append(anomaly)
        except Exception as e:
            log.warning("ML prediction failed: %s", e)

    async def _run_rl_adaptation(self, state: dict, anomalies: list[CausalAnomaly]):
        """Run RL adaptation to select optimal runtime actions."""
        try:
            from backend.core.runtime.adaptation.rl_engine import rl_adaptation_engine

            anomaly_dicts = [a.__dict__ for a in anomalies]
            rl_action = rl_adaptation_engine.select_action(state, anomaly_dicts)

            log.info(
                "RL action: isolation=%s threshold=%.2f quarantine=%s scale=%.2f",
                rl_action.isolation_mode,
                rl_action.detection_threshold,
                rl_action.quarantine,
                rl_action.resource_scale,
            )

            reward = rl_adaptation_engine.compute_reward(anomaly_dicts, 0.0)
            await rl_adaptation_engine.update(state, rl_action, reward, state)

            self._recent_rl_action = rl_action
            self._recent_rl_reward = reward
        except Exception as e:
            log.warning("RL adaptation failed: %s", e)


anomaly_detector = CausalAnomalyDetector()
