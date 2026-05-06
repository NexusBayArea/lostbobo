"""Memory API routes — wired through Kernel."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from backend.core.kernel.kernel import Kernel

router = APIRouter(prefix="/memory", tags=["memory"])
kernel = Kernel()


@router.post("/record")
async def record(payload: dict[str, Any]) -> dict[str, Any]:
    return await kernel.execute({"type": "MEMORY_RECORD", "payload": payload})


@router.post("/query")
async def query(payload: dict[str, Any]) -> dict[str, Any]:
    return await kernel.execute({"type": "MEMORY_QUERY", "payload": payload})


@router.post("/reconcile/{decision_id}")
async def reconcile(decision_id: str, observed: dict[str, Any]) -> dict[str, Any]:
    return await kernel.execute(
        {"type": "MEMORY_RECONCILE", "payload": {"decision_id": decision_id, "observed": observed}}
    )
