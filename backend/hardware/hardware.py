"""Hardware routing — FastAPI endpoints for hardware management."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/hardware", tags=["hardware"])


@router.get("/status")
async def hardware_status():
    return {"status": "operational"}
