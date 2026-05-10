"""Real-time alerting system with deduplication and escalation."""

from __future__ import annotations

import logging
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
    metadata: dict[str, Any] = field(default_factory=dict)


class RealTimeAlertingSystem:
    _instance: RealTimeAlertingSystem | None = None
    _active_alerts: dict[str, datetime] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._supabase = None
        return cls._instance

    @classmethod
    def alerts(cls) -> RealTimeAlertingSystem:
        return cls()

    async def trigger(self, anomaly: AnomalyEvent, source: str = "anomaly") -> Alert | None:
        dedup_key = f"{anomaly.entity_id}:{anomaly.anomaly_type}"

        if dedup_key in self._active_alerts:
            if datetime.now(UTC) - self._active_alerts[dedup_key] < timedelta(minutes=5):
                return None

        self._active_alerts[dedup_key] = datetime.now(UTC)

        if anomaly.severity > 0.85:
            severity = "CRITICAL"
        elif anomaly.severity > 0.6:
            severity = "WARNING"
        else:
            severity = "INFO"

        alert = Alert(
            id=f"alert_{int(datetime.now(UTC).timestamp())}",
            severity=severity,
            title=f"{anomaly.anomaly_type.replace('_', ' ').title()} Detected",
            description=anomaly.description,
            entity_id=anomaly.entity_id,
            source=source,
            confidence=anomaly.confidence,
            recommended_action=anomaly.recommended_action,
            channel=self._get_channels(severity),
            metadata=anomaly.metadata,
        )

        try:
            from backend.core.services.observability_service import observability

            obs = observability()
            obs.increment("alerts_triggered_total", {"severity": severity.lower()})
            obs.gauge("active_alerts", len(self._active_alerts))
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

    async def resolve(self, entity_id: str, anomaly_type: str) -> bool:
        dedup_key = f"{entity_id}:{anomaly_type}"
        if dedup_key in self._active_alerts:
            del self._active_alerts[dedup_key]
            return True
        return False

    def get_active_count(self) -> int:
        now = datetime.now(UTC)
        self._active_alerts = {k: v for k, v in self._active_alerts.items() if now - v < timedelta(hours=1)}
        return len(self._active_alerts)


def get_alerting_system() -> RealTimeAlertingSystem:
    return RealTimeAlertingSystem.alerts()
