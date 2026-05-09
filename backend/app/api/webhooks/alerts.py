import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alerts", tags=["webhooks"])


class AlertPayload(BaseModel):
    status: str
    alerts: list[dict[str, Any]]
    commonLabels: dict[str, str]  # noqa: N815
    commonAnnotations: dict[str, str]  # noqa: N815


@router.post("/ml-critical")
async def ml_critical_webhook(payload: AlertPayload):
    summary = payload.commonAnnotations.get("summary", "No summary")
    logger.critical("ML CRITICAL ALERT: %s", summary)
    return {"status": "received"}


@router.post("/compliance-critical")
async def compliance_critical_webhook(payload: AlertPayload):
    summary = payload.commonAnnotations.get("summary", "No summary")
    logger.critical("COMPLIANCE CRITICAL ALERT: %s", summary)
    return {"status": "received"}


@router.post("/default")
async def default_webhook(payload: AlertPayload):
    summary = payload.commonAnnotations.get("summary", "No summary")
    logger.warning("ALERT received: %s", summary)
    return {"status": "received"}


@router.post("/team-warning")
async def team_warning_webhook(payload: AlertPayload):
    summary = payload.commonAnnotations.get("summary", "No summary")
    logger.warning("TEAM WARNING ALERT: %s", summary)
    return {"status": "received"}
