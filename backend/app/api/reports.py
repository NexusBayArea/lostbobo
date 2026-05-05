from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import Literal
import uuid

router = APIRouter(prefix="/reports", tags=["Reports"])


class ReportRequest(BaseModel):
    simulation_id: str
    report_type: Literal["thermal_analysis", "robustness", "compliance", "executive", "full"]
    format: Literal["markdown", "pdf", "json"] = "markdown"
    include_raw_data: bool = False
    dag_trigger: bool = True


@router.post("/generate")
async def generate_report(request: ReportRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())

    background_tasks.add_task(process_report, job_id, request)

    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Report generation started via DAG",
    }


async def process_report(job_id: str, request: ReportRequest):
    """Background task — called by DAG completion trigger."""
    print(f"Generating report {job_id} for simulation {request.simulation_id}")