"""Auto-Research API route."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from backend.core.kernel.kernel import Kernel

router = APIRouter(prefix="/auto-research", tags=["auto-research"])
kernel = Kernel()


@router.post("/run")
async def run_research(payload: dict[str, Any]) -> dict[str, Any]:
    return await kernel.execute({"type": "AUTO_RESEARCH_RUN", "payload": payload})
