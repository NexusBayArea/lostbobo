from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class LaunchConfig(BaseModel):
    model: str
    geometry: str
    solver: str

@router.post("/launch")
async def launch_simulation(config: LaunchConfig):
    # Logic to call RunPod API and queue simulation would go here
    return {
        "status": "provisioning", 
        "job_id": "auto_generated_uuid",
        "config_received": config
    }
