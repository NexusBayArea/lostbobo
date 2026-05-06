"""Kernel Skill Registry."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class Skill:
    name: str
    kind: str
    handler: Callable


class SkillRegistry:
    def __init__(self):
        self.skills: dict[str, Skill] = {}

    def register(self, skill: Skill):
        self.skills[skill.name] = skill

    async def execute(self, name: str, input_data: dict[str, Any]):
        skill = self.skills.get(name)
        if not skill:
            raise ValueError(f"Skill {name} not found")
        return await skill.handler(input_data)
