"""Observational Memory API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from backend.core.kernel.kernel import Kernel

router = APIRouter(prefix="/observational", tags=["observational"])
kernel = Kernel()


@router.post("/observe")
async def observe_event(payload: dict[str, Any]) -> dict[str, Any]:
    return await kernel.execute({"type": "OBSERVE_EVENT", "payload": payload})


@router.post("/reflect")
async def trigger_reflect(payload: dict[str, Any]) -> dict[str, Any]:
    return await kernel.execute({"type": "REFLECT", "payload": payload})
