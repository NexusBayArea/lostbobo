"""Fat Skills Registry — typed, executable knowledge objects."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from backend.core.models.hypothesis import Hypothesis


@dataclass
class Skill:
    name: str
    kind: str
    description: str
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    execute: Callable
    success_metrics: list[str] | None


class SkillRegistry:
    """Central registry for all fat skills."""

    def __init__(self):
        self.skills: dict[str, Skill] = {}

    def register(self, skill: Skill):
        self.skills[skill.name] = skill

    def get(self, name: str) -> Skill | None:
        return self.skills.get(name)

    def list_by_kind(self, kind: str) -> list[Skill]:
        return [s for s in self.skills.values() if s.kind == kind]

    async def execute(self, name: str, inputs: dict) -> Hypothesis:
        skill = self.get(name)
        if not skill:
            raise ValueError(f"Skill {name} not found")
        result = await skill.execute(inputs)
        return result
