from __future__ import annotations

from pydantic import BaseModel


class SemanticVersion(BaseModel):
    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def parse(cls, version_str: str) -> SemanticVersion:
        parts = version_str.split(".")
        if len(parts) != 3:
            raise ValueError(f"Invalid semantic version: {version_str}")
        return cls(major=int(parts[0]), minor=int(parts[1]), patch=int(parts[2]))
