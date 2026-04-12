"""
Supabase job operations for worker service
"""

import time
from typing import Any, Dict, Optional

from app.core.db import get_supabase_client


def claim_job(worker_id: str) -> Optional[Dict[str, Any]]:
    """
    Claim a job from the queue using lease-based mechanism
    Returns job data if successfully claimed, None otherwise
    """
    supabase = get_supabase_client()

    # Generate lease ID
    lease_id = f"{worker_id}:{int(time.time())}"

    # Try to claim a job by updating its status from queued to leased
    # We'll claim the highest priority job available
    result = supabase.rpc(
        "claim_job",
        {
            "worker_id": worker_id,
            "lease_id": lease_id,
            "lease_duration": 300,  # 5 minute lease
        },
    ).execute()

    if result.data and len(result.data) > 0:
        job_data = result.data[0]
        # Add lease info to job data
        job_data["lease_id"] = lease_id
        job_data["worker_id"] = worker_id
        return job_data

    return None


def renew_lease(job_id: str, lease_id: str) -> bool:
    """
    Renew lease on a job to prevent timeout during long execution
    """
    supabase = get_supabase_client()

    result = supabase.rpc(
        "renew_lease",
        {
            "job_id": job_id,
            "lease_id": lease_id,
            "lease_duration": 300,  # 5 minute extension
        },
    ).execute()

    return result.data is not None and len(result.data) > 0


def update_job_status(
    job_id: str,
    status: str,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> bool:
    """
    Update job status in Supabase
    """
    supabase = get_supabase_client()

    update_data = {"status": status, "updated_at": "now()"}

    if result is not None:
        update_data["result"] = result

    if error is not None:
        update_data["error"] = error

    if status in ["done", "failed"]:
        update_data["completed_at"] = "now()"

    try:
        result = supabase.table("jobs").update(update_data).eq("id", job_id).execute()
        return result.data is not None and len(result.data) > 0
    except Exception:
        return False


def increment_attempt_count(job_id: str) -> bool:
    """
    Increment job attempt counter
    """
    supabase = get_supabase_client()

    # First get current attempt count
    result = supabase.table("jobs").select("attempt_count").eq("id", job_id).execute()

    if not result.data or len(result.data) == 0:
        return False

    current_count = result.data[0]["attempt_count"]

    # Update with incremented count
    update_data = {"attempt_count": current_count + 1, "updated_at": "now()"}

    try:
        result = supabase.table("jobs").update(update_data).eq("id", job_id).execute()
        return result.data is not None and len(result.data) > 0
    except Exception:
        return False


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Get job details by ID
    """
    supabase = get_supabase_client()

    result = supabase.table("jobs").select("*").eq("id", job_id).execute()

    if result.data and len(result.data) > 0:
        return result.data[0]

    return None
