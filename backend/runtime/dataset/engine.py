"""Simulation Dataset Engine — turns every run into structured, reusable data."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from backend.runtime.provenance.graph import ProvenanceGraph, ProvenanceNode

log = logging.getLogger(__name__)


@dataclass
class SimulationDatasetEntry:
    run_id: str
    query: str
    chemistry: str
    parameters: dict
    solver: str
    convergence: bool
    outputs: dict
    validation_score: float
    provenance_node_id: str


class SimulationDatasetEngine:
    """Stores and queries simulation history as a scientific dataset."""

    def __init__(self):
        self.graph = ProvenanceGraph()

    async def record_run(self, entry: SimulationDatasetEntry) -> str:
        """Record a simulation and link to provenance."""
        node = ProvenanceNode(
            node_id=entry.run_id,
            node_type="simulation",
            data={
                "query": entry.query,
                "chemistry": entry.chemistry,
                "solver": entry.solver,
                "convergence": entry.convergence,
                "validation_score": entry.validation_score,
            },
        )
        await self.graph.add_node(node)

        log.info("Dataset recorded: %s (score=%.3f)", entry.run_id, entry.validation_score)
        return entry.run_id
