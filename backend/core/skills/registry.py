"""SkillRegistry — fat skills execution layer (SOPs, simulations, policies)."""

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
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    handler: Callable


class SkillRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.skills = {}
        return cls._instance

    def register(self, skill: Skill):
        self.skills[skill.name] = skill

    def get(self, name: str) -> Skill | None:
        return self.skills.get(name)

    def list(self) -> list[Skill]:
        return list(self.skills.values())

    async def execute(self, name: str, inputs: dict[str, Any]) -> Hypothesis:
        skill = self.get(name)
        if not skill:
            raise ValueError(f"Skill '{name}' not registered")
        result = await skill.handler(inputs)
        return result
