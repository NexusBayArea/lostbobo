from fastapi import APIRouter

from backend.runtime.swarm.swarm_coordinator import PredictionQuestion, SwarmCoordinator

swarm_router = APIRouter(prefix="/swarm", tags=["Swarm"])

coordinator = SwarmCoordinator()


@swarm_router.post("/run")
async def run_swarm(payload: dict) -> dict:
    question = PredictionQuestion(**payload)
    forecast = await coordinator.run(question)
    return forecast.model_dump(mode="json")
