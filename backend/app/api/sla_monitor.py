"""SLA Monitoring Dashboard API."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.core.hardware.sla import SLAContractEngine
from backend.core.runtime.alerting.engine import RealTimeAlertingSystem

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sla", tags=["SLA Monitoring"])


@router.get("/status")
async def get_sla_status() -> dict[str, Any]:
    engine = SLAContractEngine()
    stats = await engine.get_current_sla_stats()

    return {
        "overall_compliance": stats.get("overall_compliance", 99.5),
        "by_tier": stats.get("by_tier", {}),
        "breaches_last_24h": stats.get("breaches_last_24h", 0),
        "active_isolated_reserve": stats.get("active_isolated", 0),
        "avg_queue_ms": stats.get("avg_queue_ms", 120),
        "itar_compliance_pct": stats.get("itar_compliance", 100.0),
        "warm_hit_rate": stats.get("warm_hit_rate", 94.0),
    }


@router.get("/breaches")
async def get_recent_breaches(limit: int = 50) -> list[dict[str, Any]]:
    engine = SLAContractEngine()
    return await engine.get_recent_breaches(limit)


@router.get("/health")
async def get_sla_health() -> dict[str, Any]:
    alerting = RealTimeAlertingSystem.alerts()
    active = alerting.list_active_alerts()
    sla_alerts = [a for a in active if a.group_key in ("hardware_cluster", None)]
    health = 92 if len(sla_alerts) == 0 else max(40, 95 - len(sla_alerts) * 8)

    return {
        "health_score": health,
        "active_alerts": len(sla_alerts),
        "critical_breaches": len([a for a in sla_alerts if a.severity == "CRITICAL"]),
    }


@router.get("/analytics")
async def get_sla_analytics(days: int = 30) -> dict[str, Any]:
    from backend.core.hardware.sla.analytics import SLABreachAnalytics

    analytics = SLABreachAnalytics.analytics()
    return await analytics.get_breach_report(days)


@router.get("/root-causes")
async def get_root_causes() -> list[dict[str, Any]]:
    from backend.core.hardware.sla.analytics import SLABreachAnalytics

    return await SLABreachAnalytics.analytics().get_top_root_causes()


@router.get("/breach-risk")
async def get_breach_risk(horizon_hours: int = 24) -> dict[str, Any]:
    from backend.core.hardware.sla.prediction import SLABreachPredictor

    return await SLABreachPredictor.predictor().predict_breach_risk(horizon_hours=horizon_hours)


@router.get("/stream")
async def sla_stream() -> StreamingResponse:
    async def event_generator():
        while True:
            try:
                engine = SLAContractEngine()
                stats = await engine.get_current_sla_stats()
                alerting = RealTimeAlertingSystem.alerts()
                active = alerting.list_active_alerts()
                sla_alerts = [a for a in active if a.group_key in ("hardware_cluster", None)]

                payload = json.dumps(
                    {
                        "overall_compliance": stats.get("overall_compliance", 99.5),
                        "breaches_last_24h": stats.get("breaches_last_24h", 0),
                        "active_alerts": len(sla_alerts),
                        "health_score": 92 if len(sla_alerts) == 0 else max(40, 95 - len(sla_alerts) * 8),
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                )
                yield f"data: {payload}\n\n"
            except Exception as e:
                logger.warning(f"SLA stream error: {e}")
            await asyncio.sleep(5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
