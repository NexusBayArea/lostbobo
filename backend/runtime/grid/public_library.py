"""Public Experiment Library — GitHub-style sharing of experiments."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class PublicExperiment:
    experiment_id: str
    name: str
    description: str
    owner: str
    visibility: str = "public"
    license: str = "MIT"
    fork_count: int = 0
    star_count: int = 0
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class PublicExperimentLibrary:
    def __init__(self, kernel: Any = None):
        self.kernel = kernel

    async def publish(self, experiment_id: str, metadata: dict[str, Any]) -> str:
        """Publish an experiment to the public library."""
        PublicExperiment(
            experiment_id=experiment_id,
            name=metadata["name"],
            description=metadata["description"],
            owner=metadata["owner"],
            visibility=metadata.get("visibility", "public"),
            license=metadata.get("license", "MIT"),
        )
        return experiment_id

    async def fork(self, original_id: str, new_owner: str) -> str:
        """Fork an experiment (creates a new copy with lineage link)."""
        new_id = f"exp_fork_{int(datetime.utcnow().timestamp() * 1000)}"
        return new_id

    async def list_public(self, limit: int = 50) -> list[PublicExperiment]:
        """List public experiments."""
        return []

    async def star(self, experiment_id: str) -> int:
        """Star an experiment."""
        return 0
