import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.app.core.supabase import supabase as supabase_client


# Dummy auth dependency for now; assumes verify_auth logic is managed globally or imported
async def verify_auth():
    # Placeholder for actual auth verification
    return {"id": "user-123"}


router = APIRouter(prefix="/alpha", tags=["Alpha Control"])

# 1. Define valid options (Must match src/lib/contract.ts)
ModelType = Literal["Parametric Sweep", "Latin Hypercube", "Sobol GSA"]
GeometryType = Literal["Turbine Blade", "Heat Sink", "Pressure Vessel"]
SolverType = Literal["MFEM (Structural)", "SUNDIALS (Thermal)", "Mercury-Hybrid"]


class LaunchRequest(BaseModel):
    model_config: ModelType
    target_geometry: GeometryType
    physics_solver: SolverType


@router.post("/launch")
async def launch_simulation(request: LaunchRequest, user: dict = Depends(verify_auth)):  # noqa: B008
    job_id = f"job_{uuid.uuid4().hex[:6]}"

    # 2. Persist to Supabase so it shows up in AdminAnalyticsPage
    try:
        supabase_client.table("simulation_history").insert(
            {
                "job_id": job_id,
                "user_id": user["id"],
                "status": "queued",
                "progress": 0,
                "model_config": request.model_config,
                "target_geometry": request.target_geometry,
                "physics_solver": request.physics_solver,
            }
        ).execute()

        return {"status": "success", "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
