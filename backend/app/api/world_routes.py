"""World Model API routes — wired through Kernel."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from backend.core.kernel.kernel import Kernel

router = APIRouter(prefix="/world_model", tags=["world_model"])
kernel = Kernel()


@router.post("/update")
async def update(payload: dict[str, Any]) -> dict[str, Any]:
    return await kernel.execute({"type": "WORLD_UPDATE", "payload": payload})


@router.post("/simulate")
async def simulate(payload: dict[str, Any]) -> dict[str, Any]:
    return await kernel.execute({"type": "SKILL_EXECUTE", "payload": {"skill": "simulate", "input": payload}})


@router.post("/propagate")
async def propagate(payload: dict[str, Any]) -> dict[str, Any]:
    return await kernel.execute({"type": "WORLD_PROPAGATE", "payload": payload})
