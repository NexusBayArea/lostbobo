import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.deps import get_supabase_client
from app.core.queue import enqueue_job

router = APIRouter()


class JobCreate(BaseModel):
    payload: Dict[str, Any]
    priority: int = 0
    idempotency_key: Optional[str] = None


class JobResponse(BaseModel):
    id: str
    status: str


@router.post("/jobs", response_model=JobResponse)
async def create_job(job: JobCreate, supabase=Depends(get_supabase_client)):
    """Accept job requests, validate payloads, assign priority, write to Supabase, return job ID"""
    # Validate payload
    if not job.payload:
        raise HTTPException(status_code=400, detail="Payload cannot be empty")

    # Generate job ID
    job_id = str(uuid.uuid4())

    # Prepare job data
    job_data = {
        "id": job_id,
        "payload": job.payload,
        "status": "queued",
        "priority": job.priority,
        "fingerprint": None,  # Will be computed if needed
        "attempt_count": 0,
    }

    # Insert job into Supabase
    result = supabase.table("jobs").insert(job_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create job")

    # Enqueue job for processing
    enqueue_job(job_id, job.priority)

    return JobResponse(id=job_id, status="queued")


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, supabase=Depends(get_supabase_client)):
    """Get job status"""
    result = supabase.table("jobs").select("id, status").eq("id", job_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Job not found")

    job = result.data[0]
    return JobResponse(id=job["id"], status=job["status"])
