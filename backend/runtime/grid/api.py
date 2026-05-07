"""Experiment Grid API Routes."""

from __future__ import annotations

from fastapi import APIRouter

from backend.runtime.discovery.graph import DiscoveryGraph
from backend.runtime.grid.intelligence import ExperimentIntelligence
from backend.runtime.grid.registry import ExperimentRegistry
from backend.runtime.grid.scheduler import SwarmScheduler

router = APIRouter(prefix="/api/v1/grid", tags=["experiment-grid"])

registry = ExperimentRegistry()
scheduler = SwarmScheduler()
graph = DiscoveryGraph()
intelligence = ExperimentIntelligence(discovery_graph=graph)


@router.post("/experiments/register")
async def register_experiment(payload: dict):
    exp_id = await registry.register(**payload)
    return {"experimentId": exp_id, "status": "registered"}


@router.post("/scheduler/allocate")
async def allocate_swarm(payload: dict):
    swarm_id = await scheduler.allocate_swarm(**payload)
    return {"swarmId": swarm_id, "status": "allocated"}


@router.get("/intelligence/suggest")
async def suggest_next_swarm(experiment_id: str, objective: str = "general"):
    return await intelligence.suggest_next_swarm(experiment_id, objective)
