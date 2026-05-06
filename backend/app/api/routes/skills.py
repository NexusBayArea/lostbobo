"""Skill API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from backend.core.skills.registry import SkillRegistry

router = APIRouter(prefix="/skills", tags=["skills"])
registry = SkillRegistry()


@router.get("/list")
async def list_skills() -> dict[str, Any]:
    return {"skills": [{"name": s.name, "kind": s.kind} for s in registry.list()]}


@router.post("/execute/{name}")
async def execute_skill(name: str, inputs: dict[str, Any]) -> dict[str, Any]:
    result = await registry.execute(name, inputs)
    return {"id": result.id}
