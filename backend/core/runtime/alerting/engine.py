"""Real-time alerting system with deduplication and escalation."""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from backend.core.runtime.anomaly.engine import AnomalyEvent

logger = logging.getLogger(__name__)


@dataclass
class Alert:
    id: str
    severity: str
    title: str
    description: str
    entity_id: str
    source: str
    confidence: float
    recommended_action: str
    channel: list[str] = field(default_factory=list)
    group_key: str | None = None
    status: str = "ACTIVE"
    acknowledged_at: datetime | None = None
    acknowledged_by: str | None = None
    notes: str | None = None
    resolved_at: datetime | None = None
    resolution_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class AlertFatigueGuard:
    _instance: AlertFatigueGuard | None = None
    _alert_history: dict[str, list[datetime]] = defaultdict(list)
    _suppression_rules: dict[str, timedelta] = {}
    _user_feedback: dict[str, int] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def guard(cls) -> AlertFatigueGuard:
        return cls()

    def should_suppress(self, anomaly: AnomalyEvent) -> bool:
        pattern_key = f"{anomaly.anomaly_type}:{anomaly.entity_id[:8] if anomaly.entity_id else 'unknown'}"

        cooldown = self._suppression_rules.get(pattern_key, timedelta(minutes=8))
        if pattern_key in self._alert_history:
            last = self._alert_history[pattern_key][-1]
            if datetime.now(UTC) - last < cooldown:
                return True

        recent = [t for t in self._alert_history[pattern_key] if datetime.now(UTC) - t < timedelta(hours=2)]
        if len(recent) >= 5:
            self._user_feedback[pattern_key] = self._user_feedback.get(pattern_key, 0) + 1
            return True

        if anomaly.confidence < 0.65 and anomaly.severity < 0.75:
            return True

        if self._user_feedback.get(pattern_key, 0) >= 3:
            self._suppression_rules[pattern_key] = timedelta(hours=4)
            return True

        return False

    def record_alert(self, alert: Alert) -> None:
        key = f"{alert.source}:{alert.entity_id[:8] if alert.entity_id else 'unknown'}"
        self._alert_history[key].append(datetime.now(UTC))
        if len(self._alert_history[key]) > 50:
            self._alert_history[key] = self._alert_history[key][-50:]

    def get_frequency(self, pattern_key: str) -> int:
        recent = [t for t in self._alert_history[pattern_key] if datetime.now(UTC) - t < timedelta(hours=2)]
        return len(recent)

    def record_positive_feedback(self, alert: Alert) -> None:
        key = f"{alert.source}:{alert.entity_id[:8] if alert.entity_id else 'unknown'}"
        self._user_feedback[key] = max(0, self._user_feedback.get(key, 0) - 1)

    def record_resolution_feedback(self, alert: Alert) -> None:
        if not alert.resolved_at or not alert.acknowledged_at:
            return
        resolution_time = (alert.resolved_at - alert.acknowledged_at).total_seconds() / 60
        key = f"{alert.source}:{alert.entity_id[:8] if alert.entity_id else 'unknown'}"
        if resolution_time < 10:
            self._user_feedback[key] = self._user_feedback.get(key, 0) + 2


class RealTimeAlertingSystem:
    _instance: RealTimeAlertingSystem | None = None
    _active_alerts: dict[str, datetime] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._supabase = None
            cls._instance._alert_store: dict[str, Alert] = {}
        return cls._instance

    @classmethod
    def alerts(cls) -> RealTimeAlertingSystem:
        return cls()

    def _store_alert(self, alert: Alert) -> None:
        self._alert_store[alert.id] = alert

    def _compute_dynamic_severity(self, anomaly: AnomalyEvent) -> str:
        try:
            from backend.core.runtime.state_registry.service import StateRegistryService

            state = await StateRegistryService.registry().get_current()
            regime = getattr(state, "regime", "normal")
        except Exception:
            regime = "normal"

        if anomaly.severity > 0.85:
            return "CRITICAL"
        if anomaly.severity > 0.6:
            return "WARNING"

        if regime == "normal" and anomaly.severity < 0.8:
            return "INFO"
        return "WARNING"

    def _compute_group_key(self, anomaly: AnomalyEvent) -> str | None:
        if "node" in anomaly.entity_id.lower():
            return "hardware_cluster"
        if "economic" in anomaly.anomaly_type.lower():
            return "economics"
        return None

    async def trigger(self, anomaly: AnomalyEvent, source: str = "anomaly") -> Alert | None:
        guard = AlertFatigueGuard.guard()

        if guard.should_suppress(anomaly):
            try:
                from backend.core.services.observability_service import observability

                observability().increment("alerts_suppressed_fatigue")
            except Exception:
                pass
            return None

        severity = self._compute_dynamic_severity(anomaly)

        dedup_key = f"{anomaly.entity_id}:{anomaly.anomaly_type}"
        if dedup_key in self._active_alerts:
            if datetime.now(UTC) - self._active_alerts[dedup_key] < timedelta(minutes=5):
                return None

        self._active_alerts[dedup_key] = datetime.now(UTC)

        alert = Alert(
            id=f"alert_{int(datetime.now(UTC).timestamp())}",
            severity=severity,
            title=f"{anomaly.anomaly_type.replace('_', ' ').title()}",
            description=anomaly.description,
            entity_id=anomaly.entity_id,
            source=source,
            confidence=anomaly.confidence,
            recommended_action=anomaly.recommended_action,
            channel=self._get_channels(severity),
            group_key=self._compute_group_key(anomaly),
            metadata=anomaly.metadata,
        )

        guard.record_alert(alert)
        self._store_alert(alert)

        try:
            from backend.core.services.observability_service import observability

            obs = observability()
            obs.increment("alerts_triggered_total", {"severity": severity.lower()})
            obs.gauge("active_alerts", len(self._active_alerts))
            pattern_key = f"{anomaly.anomaly_type}:{anomaly.entity_id[:8] if anomaly.entity_id else 'unknown'}"
            obs.gauge("alert_frequency_per_pattern", guard.get_frequency(pattern_key), {"pattern": pattern_key})
        except Exception:
            pass

        try:
            from backend.core.runtime.event_fabric.log import EventLogService
            from backend.core.runtime.event_fabric.schema import SimHPCEvent

            await EventLogService.event_log().publish(
                SimHPCEvent(
                    event_type="alert.triggered",
                    source_plugin="kernel",
                    confidence=alert.confidence,
                    payload={
                        "id": alert.id,
                        "severity": alert.severity,
                        "title": alert.title,
                        "entity_id": alert.entity_id,
                        "source": alert.source,
                    },
                )
            )
        except Exception:
            pass

        try:
            import asyncio

            asyncio.create_task(self._dispatch_notifications(alert))
        except Exception:
            pass

        return alert

    def _get_channels(self, severity: str) -> list[str]:
        if severity == "CRITICAL":
            return ["pagerduty", "slack"]
        if severity == "WARNING":
            return ["slack"]
        return ["slack"]

    async def _dispatch_notifications(self, alert: Alert) -> None:
        if "slack" in alert.channel:
            await self._send_slack(alert)
        if "pagerduty" in alert.channel:
            await self._send_pagerduty(alert)

    async def _send_slack(self, alert: Alert) -> None:
        try:
            from backend.core.infisical import get_secret

            webhook = get_secret("SLACK_WEBHOOK_URL", "")
            if not webhook:
                return

            import aiohttp

            payload = {
                "text": f"[{alert.severity}] {alert.title}",
                "attachments": [
                    {
                        "color": "#ff0000" if alert.severity == "CRITICAL" else "#ffaa00",
                        "fields": [
                            {"title": "Entity", "value": alert.entity_id, "short": True},
                            {"title": "Source", "value": alert.source, "short": True},
                            {"title": "Action", "value": alert.recommended_action, "short": False},
                        ],
                    }
                ],
            }
            async with aiohttp.ClientSession() as session:
                await session.post(webhook, json=payload)
        except Exception as e:
            logger.warning(f"Slack notification failed: {e}")

    async def _send_pagerduty(self, alert: Alert) -> None:
        try:
            from backend.core.infisical import get_secret

            routing_key = get_secret("PAGERDUTY_ROUTING_KEY", "")
            if not routing_key:
                return

            import aiohttp

            payload = {
                "routing_key": routing_key,
                "event_action": "trigger",
                "payload": {
                    "summary": f"[{alert.severity}] {alert.title}",
                    "source": alert.source,
                    "severity": "critical" if alert.severity == "CRITICAL" else "warning",
                },
            }
            async with aiohttp.ClientSession() as session:
                await session.post("https://events.pagerduty.com/v2/enqueue", json=payload)
        except Exception as e:
            logger.warning(f"PagerDuty notification failed: {e}")

    def get_active_count(self) -> int:
        now = datetime.now(UTC)
        self._active_alerts = {k: v for k, v in self._active_alerts.items() if now - v < timedelta(hours=1)}
        return len(self._active_alerts)

    async def acknowledge(
        self,
        alert_id: str,
        user: str,
        notes: str | None = None,
        escalate: bool = False,
    ) -> bool:
        guard = AlertFatigueGuard.guard()
        stored = self._alert_store.get(alert_id)
        if not stored:
            return False

        stored.status = "ESCALATED" if escalate else "ACKNOWLEDGED"
        stored.acknowledged_at = datetime.now(UTC)
        stored.acknowledged_by = user
        stored.notes = notes
        self._alert_store[alert_id] = stored

        try:
            from backend.core.services.observability_service import observability

            observability().increment("alerts_acknowledged_total")
        except Exception:
            pass

        try:
            from backend.core.runtime.event_fabric.log import EventLogService
            from backend.core.runtime.event_fabric.schema import SimHPCEvent

            await EventLogService.event_log().publish(
                SimHPCEvent(
                    event_type="alert.acknowledged",
                    source_plugin="kernel",
                    confidence=stored.confidence,
                    payload={
                        "alert_id": alert_id,
                        "user": user,
                        "escalated": escalate,
                        "notes": notes,
                    },
                )
            )
        except Exception:
            pass

        if not escalate:
            guard.record_positive_feedback(stored)

        return True

    async def resolve(
        self,
        alert_id: str,
        user: str,
        resolution_reason: str,
    ) -> bool:
        stored = self._alert_store.get(alert_id)
        if not stored:
            return False

        stored.status = "RESOLVED"
        stored.resolved_at = datetime.now(UTC)
        stored.resolution_reason = resolution_reason
        self._alert_store[alert_id] = stored

        try:
            from backend.core.runtime.event_fabric.log import EventLogService
            from backend.core.runtime.event_fabric.schema import SimHPCEvent

            resolution_time = 0.0
            if stored.resolved_at and stored.acknowledged_at:
                resolution_time = (stored.resolved_at - stored.acknowledged_at).total_seconds() / 60

            await EventLogService.event_log().publish(
                SimHPCEvent(
                    event_type="alert.resolved",
                    source_plugin="kernel",
                    confidence=stored.confidence,
                    payload={
                        "alert_id": alert_id,
                        "user": user,
                        "reason": resolution_reason,
                        "resolution_time_minutes": resolution_time,
                    },
                )
            )
        except Exception:
            pass

        AlertFatigueGuard.guard().record_resolution_feedback(stored)
        return True

    def get_alert(self, alert_id: str) -> Alert | None:
        return self._alert_store.get(alert_id)

    def list_active_alerts(self) -> list[Alert]:
        return [a for a in self._alert_store.values() if a.status in ("ACTIVE", "ACKNOWLEDGED")]


def get_alerting_system() -> RealTimeAlertingSystem:
    return RealTimeAlertingSystem.alerts()
