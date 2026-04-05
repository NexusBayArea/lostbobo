from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Header
from typing import Optional, Any, Dict
import uuid
import json
import os
import logging
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

# Shared dependencies imported at module level
# These are set by the main app during startup
supabase_client: Any = None
r_client: Any = None
verify_auth: Any = None
enqueue_job: Any = None
get_job: Any = None
set_job: Any = None
update_job_field: Any = None
PLAN_LIMITS: Any = None
UserPlan: Any = None
record_simulation_start: Any = None
validate_simulation_request: Any = None
check_plan_limits: Any = None
check_idempotency: Any = None
store_idempotency: Any = None
check_concurrent_runs: Any = None
increment_user_usage: Any = None
get_user_usage: Any = None
check_rate_limit_fn: Any = None
get_weekly_usage_fn: Any = None
WEEKLY_LIMIT: int = 10


def init_routes(
    supabase,
    redis,
    auth_dep,
    enqueue,
    get_j,
    set_j,
    update_jf,
    plan_limits,
    user_plan,
    record_sim,
    validate_sim,
    check_limits,
    check_idem,
    store_idem,
    check_concurrent,
    increment_usage,
    get_usage,
    rate_limit_fn=None,
    weekly_usage_fn=None,
    weekly_limit=10,
):
    global supabase_client, r_client, verify_auth, enqueue_job, get_job, set_job
    global update_job_field, PLAN_LIMITS, UserPlan, record_simulation_start
    global validate_simulation_request, check_plan_limits, check_idempotency
    global \
        store_idempotency, \
        check_concurrent_runs, \
        increment_user_usage, \
        get_user_usage
    global check_rate_limit_fn, get_weekly_usage_fn, WEEKLY_LIMIT
    supabase_client = supabase
    r_client = redis
    verify_auth = auth_dep
    enqueue_job = enqueue
    get_job = get_j
    set_job = set_j
    update_job_field = update_jf
    PLAN_LIMITS = plan_limits
    UserPlan = user_plan
    record_simulation_start = record_sim
    validate_simulation_request = validate_sim
    check_plan_limits = check_limits
    check_idempotency = check_idem
    store_idempotency = store_idem
    check_concurrent_runs = check_concurrent
    increment_user_usage = increment_usage
    get_user_usage = get_usage
    check_rate_limit_fn = rate_limit_fn
    get_weekly_usage_fn = weekly_usage_fn
    WEEKLY_LIMIT = weekly_limit


@router.post("/simulations", tags=["Simulations"])
async def create_simulation(
    prompt: Optional[str] = None,
    input_params: Optional[Dict[str, Any]] = None,
    scenario_name: Optional[str] = None,
    user: dict = Depends(verify_auth),
):
    """Create a new simulation and enqueue it to Redis."""
    user_id = user["user_id_internal"]
    plan = user.get("plan", UserPlan.FREE)
    limits = PLAN_LIMITS[plan]

    # 1. Rate limit — prevent spam clicking (10s cooldown)
    if check_rate_limit_fn:
        check_rate_limit_fn(user_id)

    # 2. Weekly limit — max 10 runs per rolling 7 days (free tier)
    if get_weekly_usage_fn and plan == UserPlan.FREE:
        weekly_used = await get_weekly_usage_fn(user_id)
        if weekly_used >= WEEKLY_LIMIT:
            raise HTTPException(
                status_code=429,
                detail={
                    "message": "Weekly simulation limit reached",
                    "limit": WEEKLY_LIMIT,
                    "used": weekly_used,
                    "remaining": 0,
                },
            )

    # 3. (Removed Redis-based usage check - using Supabase as single source of truth)

    # Check concurrent runs
    has_running = await check_concurrent_runs(user_id)
    if has_running and plan == UserPlan.FREE:
        raise HTTPException(409, "Free tier allows only one concurrent simulation.")

    sim_id = str(uuid.uuid4())

    # Write to Supabase simulations table
    if supabase_client:
        try:
            supabase_client.table("simulations").insert(
                {
                    "id": sim_id,
                    "job_id": sim_id,
                    "user_id": user_id if user["type"] != "api_key" else None,
                    "status": "queued",
                    "prompt": prompt,
                    "input_params": input_params or {},
                    "scenario_name": scenario_name or "Custom Simulation",
                }
            ).execute()
        except Exception as e:
            logger.error(f"Failed to insert simulation: {e}")

    # Enqueue to Redis
    job_data = {
        "id": sim_id,
        "user_id": user_id,
        "is_paid": plan != UserPlan.FREE,
        "prompt": prompt,
        "input_params": input_params or {},
        "scenario_name": scenario_name or "Custom Simulation",
    }
    enqueue_job(sim_id, job_data)
    await increment_user_usage(user_id)

    return {
        "simulation_id": sim_id,
        "status": "queued",
        "message": "Simulation queued. Track progress in your dashboard.",
    }


@router.get("/simulations", tags=["Simulations"])
async def list_simulations(
    limit: int = 20,
    user: dict = Depends(verify_auth),
):
    """List user's simulations from Redis (fast path) or Supabase."""
    user_id = user["user_id_internal"]
    results = []

    # Scan Redis for user's jobs
    keys = r_client.keys("job:*")
    for k in keys:
        job = r_client.hgetall(k)
        if job.get("user_id") == user_id:
            results.append(
                {
                    "id": k.split(":")[1],
                    "status": job.get("status"),
                    "scenario_name": job.get("scenario_name", "Unknown"),
                    "created_at": job.get("created_at", ""),
                }
            )

    results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return results[:limit]


@router.get("/simulations/{sim_id}", tags=["Simulations"])
async def get_simulation(
    sim_id: str,
    user: dict = Depends(verify_auth),
):
    """Get a single simulation's full state."""
    job = get_job(sim_id)
    if not job:
        raise HTTPException(404, "Simulation not found")

    # Verify ownership
    if job.get("user_id") != user["user_id_internal"] and user["type"] != "api_key":
        raise HTTPException(403, "Access denied")

    return job


@router.post("/simulations/{sim_id}/export-pdf", tags=["Simulations"])
async def export_pdf(
    sim_id: str,
    user: dict = Depends(verify_auth),
):
    """Get the PDF download URL for a completed simulation."""
    job = get_job(sim_id)
    if not job:
        raise HTTPException(404, "Simulation not found")
    if job.get("status") != "completed":
        raise HTTPException(409, "Simulation not yet completed")

    pdf_url = job.get("pdf_url") or job.get("report_url")
    if not pdf_url:
        raise HTTPException(404, "PDF not available")

    return {"pdf_url": pdf_url, "simulation_id": sim_id}


@router.get("/simulations/usage", tags=["Simulations"])
async def get_usage(
    user: dict = Depends(verify_auth),
):
    """Get user's weekly simulation usage."""
    user_id = user["user_id_internal"]
    usage = await get_user_usage(user_id)
    return {
        "used": usage.get("runs_used", 0),
        "limit": 10,  # Explicitly using the requested limit
        "remaining": max(0, 10 - usage.get("runs_used", 0)),
    }


@router.get("/simulations/{sim_id}/status", tags=["Simulations"])
async def get_simulation_status(
    sim_id: str,
    user: dict = Depends(verify_auth),
):
    """Get simulation status (lightweight polling endpoint)."""
    job = get_job(sim_id)
    if not job:
        raise HTTPException(404, "Simulation not found")
    return {
        "id": sim_id,
        "status": job.get("status"),
        "progress": job.get("progress", {}),
        "created_at": job.get("created_at", ""),
        "completed_at": job.get("completed_at"),
        "error": job.get("error"),
    }
