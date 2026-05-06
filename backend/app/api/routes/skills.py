"""Skill API routes — wired through Kernel."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from backend.core.kernel.kernel import Kernel

router = APIRouter(prefix="/skills", tags=["skills"])
kernel = Kernel()


@router.get("/list")
async def list_skills() -> dict[str, Any]:
    return {"skills": list(kernel.skills.skills.keys())}


@router.post("/execute/{name}")
async def execute_skill(name: str, input_data: dict[str, Any]) -> dict[str, Any]:
    return await kernel.execute({"type": "SKILL_EXECUTE", "payload": {"skill": name, "input": input_data}})
