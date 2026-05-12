from __future__ import annotations

import time

from pydantic import BaseModel

from backend.core.runtime.anomaly.detector import CausalAnomalyDetector
from backend.core.runtime.event_fabric.log import EventLogService
from backend.core.trust.telemetry_hook import TrustTelemetry


class TrustScoreBreakdown(BaseModel):
    signature_valid: bool
    capability_match: bool
    historical_anomaly_score: float
    network_deviation: float
    recursive_spawn_risk: float
    memory_access_pattern_score: float
    trust_score: float
    action: str


class BehavioralTrustEvaluator:
    def __init__(
        self,
        event_log: EventLogService | None = None,
        anomaly_detector: CausalAnomalyDetector | None = None,
        graph_store: object = None,
        world_fabric: object = None,
        telemetry: TrustTelemetry | None = None,
    ):
        self.anomaly_detector = anomaly_detector or CausalAnomalyDetector()
        self.event_log = event_log or EventLogService.event_log()
        self.graph_store = graph_store
        self.world_fabric = world_fabric
        self.telemetry = telemetry or TrustTelemetry()

        self.W_ANOMALY = 0.4
        self.W_NETWORK = 0.2
        self.W_SPAWN = 0.2
        self.W_MEMORY = 0.2

    async def evaluate(
        self,
        source_id: str,
        target_id: str | None = None,
        identity_ok: bool = True,
        capabilities_ok: bool = True,
        profile_data: dict | None = None,
    ) -> TrustScoreBreakdown:
        anomaly_score = await self._compute_anomaly_score(source_id)
        network_dev = await self._compute_network_deviation(source_id)
        spawn_risk = await self._compute_spawn_risk(source_id)
        memory_score = await self._compute_memory_pattern_score(source_id)

        weighted = (
            (1.0 - anomaly_score) * self.W_ANOMALY
            + (1.0 - network_dev) * self.W_NETWORK
            + (1.0 - spawn_risk) * self.W_SPAWN
            + (1.0 - memory_score) * self.W_MEMORY
        )

        if not identity_ok or not capabilities_ok:
            weighted = min(weighted, 0.3)

        action = self._score_to_action(weighted)

        result = TrustScoreBreakdown(
            signature_valid=identity_ok,
            capability_match=capabilities_ok,
            historical_anomaly_score=round(anomaly_score, 4),
            network_deviation=round(network_dev, 4),
            recursive_spawn_risk=round(spawn_risk, 4),
            memory_access_pattern_score=round(memory_score, 4),
            trust_score=round(weighted, 4),
            action=action,
        )

        await self.telemetry.report("trust.evaluated", source_id, result.model_dump())

        return result

    async def update_trust(
        self, plugin_id: str, anomaly_count: int = 0, last_score: float = 0.5, last_eval_time: float | None = None
    ) -> float:
        """Apply time-based decay and anomaly penalty to a trust score."""
        import math

        now = time.time()
        last_eval = last_eval_time or now
        hours_passed = (now - last_eval) / 3600
        score = last_score * math.exp(-0.02 * hours_passed)
        score -= anomaly_count * 0.05
        return max(0.0, min(1.0, score))

    async def _compute_anomaly_score(self, plugin_id: str) -> float:
        if not hasattr(self.anomaly_detector, "_recent_anomalies"):
            return 0.07
        anomalies = self.anomaly_detector._recent_anomalies or []
        plugin_anomalies = [a for a in anomalies if plugin_id in a.affected_entity_keys]
        if not plugin_anomalies:
            return 0.07
        return min(1.0, len(plugin_anomalies) * 0.15)

    async def _compute_network_deviation(self, plugin_id: str) -> float:
        return 0.02

    async def _compute_spawn_risk(self, plugin_id: str) -> float:
        return 0.01

    async def _compute_memory_pattern_score(self, plugin_id: str) -> float:
        return 0.05

    def _score_to_action(self, score: float) -> str:
        if score >= 0.9:
            return "allow"
        elif score >= 0.7:
            return "restrict"
        elif score >= 0.4:
            return "sandbox"
        else:
            return "reject"
