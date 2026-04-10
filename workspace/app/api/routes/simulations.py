from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional, Any, Dict
from pydantic import BaseModel
import uuid
import json
import os
import time
import logging
import asyncio
import httpx
from datetime import datetime

# Import add_usage_event from parent module for Authority Alignment
from app.api import add_usage_event

router = APIRouter()
logger = logging.getLogger(__name__)


class SimulationConfigPayload(BaseModel):
    parameters: Optional[list] = None
    sampling: Optional[dict] = None


class RobustnessRunRequest(BaseModel):
    scenario_name: Optional[str] = None
    config: Optional[SimulationConfigPayload] = None
    prompt: Optional[str] = None
    input_params: Optional[Dict[str, Any]] = None


def verify_auth(authorization: str = Header(None)) -> dict:
    """Stub replaced by init_routes(). If called, app wasn't initialized."""
    raise RuntimeError("verify_auth not initialized — call init_routes() first")


def check_concurrent_runs(user_id: str) -> bool:
    """Stub replaced by init_routes()."""
    raise RuntimeError("check_concurrent_runs not initialized")


async def increment_user_usage(user_id: str) -> None:
    """Stub replaced by init_routes()."""
    raise RuntimeError("increment_user_usage not initialized")


async def get_user_usage(user_id: str) -> dict:
    """Stub replaced by init_routes()."""
    raise RuntimeError("get_user_usage not initialized")


async def check_compute_availability_fn():
    """Stub replaced by init_routes()."""
    raise RuntimeError("check_compute_availability_fn not initialized")


async def reserve_idempotency_fn(user_id: str, key: str, sim_id: str) -> bool:
    """Stub replaced by init_routes()."""
    raise RuntimeError("reserve_idempotency_fn not initialized")


async def get_idempotency_value_fn(user_id: str, key: str) -> Optional[str]:
    """Stub replaced by init_routes()."""
    raise RuntimeError("get_idempotency_value_fn not initialized")


def increment_active_runs_fn(user_id: str):
    """Stub replaced by init_routes()."""
    raise RuntimeError("increment_active_runs_fn not initialized")


def decrement_active_runs_fn(user_id: str):
    """Stub replaced by init_routes()."""
    raise RuntimeError("decrement_active_runs_fn not initialized")


# Shared dependencies imported at module level
# These are set by the main app during startup
supabase_client: Any = None
r_client: Any = None
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
telemetry_queue: Any = None
http_client: Any = None
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
    telemetry_queue_ref=None,
    compute_availability_fn=None,
    reserve_idempotency_fn_ref=None,
    get_idempotency_value_fn_ref=None,
    increment_active_runs_fn_ref=None,
    decrement_active_runs_fn_ref=None,
    http_client_ref=None,
):
    global supabase_client, r_client, verify_auth, enqueue_job, get_job, set_job
    global update_job_field, PLAN_LIMITS, UserPlan, record_simulation_start
    global validate_simulation_request, check_plan_limits, check_idempotency
    global \
        store_idempotency, \
        check_concurrent_runs, \
        increment_user_usage, \
        get_user_usage, \
        check_compute_availability_fn
    global check_rate_limit_fn, get_weekly_usage_fn, WEEKLY_LIMIT, telemetry_queue
    global \
        reserve_idempotency_fn, \
        get_idempotency_value_fn, \
        increment_active_runs_fn, \
        decrement_active_runs_fn, \
        http_client

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
    telemetry_queue = telemetry_queue_ref
    check_compute_availability_fn = compute_availability_fn
    reserve_idempotency_fn = reserve_idempotency_fn_ref
    get_idempotency_value_fn = get_idempotency_value_fn_ref
    increment_active_runs_fn = increment_active_runs_fn_ref
    decrement_active_runs_fn = decrement_active_runs_fn_ref
    http_client = http_client_ref


# --- INTERNAL: RunPod Job Client ---
class RunPodJobClient:
    """Client for submitting and polling RunPod jobs (async)."""

    def __init__(
        self,
        api_key: str = None,
        pod_id: str = None,
        http_client: httpx.AsyncClient = None,
    ):
        self.api_key = api_key or os.getenv("RUNPOD_API_KEY")
        self.pod_id = pod_id or os.getenv("RUNPOD_POD_ID")
        self.base_url = "https://api.runpod.ai/v2"
        self._client = http_client

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            return httpx.AsyncClient(timeout=30.0)
        return self._client

    async def run_job(self, payload: dict) -> str:
        """Submit a job to RunPod and return job ID."""
        if not self.api_key or not self.pod_id:
            raise RuntimeError("RUNPOD_API_KEY or RUNPOD_POD_ID not configured")

        url = f"{self.base_url}/{self.pod_id}/run"

        try:
            client = await self._get_client()
            response = await client.post(
                url,
                json={"input": payload},
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            job_id = data.get("id")
            logger.info(f"Submitted job to RunPod: {job_id}")
            return job_id
        except Exception as e:
            logger.error(f"Failed to submit RunPod job: {e}")
            raise RuntimeError(f"Job submission failed: {e}")

    async def get_job_status(self, job_id: str) -> dict:
        """Poll job status from RunPod."""
        if not self.api_key or not self.pod_id:
            raise RuntimeError("RUNPOD_API_KEY or RUNPOD_POD_ID not configured")

        url = f"{self.base_url}/{self.pod_id}/status/{job_id}"

        try:
            client = await self._get_client()
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get job status: {e}")
            return {"status": "UNKNOWN", "error": str(e)}

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job."""
        if not self.api_key:
            return False

        url = f"{self.base_url}/{self.pod_id}/cancel/{job_id}"

        try:
            client = await self._get_client()
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10.0,
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to cancel job: {e}")
            return False


# Retry configuration
MAX_ATTEMPTS = 3
BACKOFF_BASE = 2
RETRYABLE_ERRORS = ["timeout", "connection", "rate limit", "transient"]


def is_retryable_error(error: str) -> bool:
    """Check if error is transient and worth retrying."""
    error_lower = error.lower()
    return any(x in error_lower for x in RETRYABLE_ERRORS)


async def acquire_lock(run_id: str, ttl: int = 300) -> bool:
    """Acquire distributed lock for job processing."""
    lock_key = f"lock:{run_id}"
    try:
        result = r_client.setnx(lock_key, "1")
        if result:
            r_client.expire(lock_key, ttl)
        return bool(result)
    except Exception as e:
        logger.warning(f"Lock acquisition failed: {e}")
        return True  # Allow on lock failure


def release_lock(run_id: str):
    """Release distributed lock."""
    lock_key = f"lock:{run_id}"
    try:
        r_client.delete(lock_key)
    except Exception:
        pass


# --- INTERNAL: background execution pipeline ---
async def run_simulation_pipeline(run_id: str, payload: dict, user_id: str):
    """Background task that runs simulation with RunPod integration, retry logic, and crash recovery."""

    # Acquire distributed lock to prevent duplicate execution
    if not await acquire_lock(run_id):
        logger.info(f"Job {run_id} already being processed, skipping")
        return

    attempt = int(get_job_field(run_id, "attempt") or 0)
    runpod_job_id = get_job_field(run_id, "runpod_job_id")

    try:
        logger.info(f"Starting pipeline for run_id={run_id}, attempt={attempt + 1}")

        # Step 1: Update job status to running
        update_job_field(run_id, "status", "running")
        update_job_field(run_id, "attempt", attempt + 1)

        # Step 2: Record in Supabase (triggers realtime)
        if record_simulation_start:
            record_simulation_start(
                run_id,
                user_id,
                payload.get("scenario_name", "Robustness Run"),
            )

        # Step 3: Enqueue to Redis for local worker (fallback)
        if enqueue_job:
            enqueue_job(run_id, payload)

        # Step 4: Submit to RunPod if configured
        client = RunPodJobClient(http_client=http_client)

        if client.api_key and client.pod_id and not runpod_job_id:
            try:
                runpod_job_id = await client.run_job(payload)
                update_job_field(run_id, "runpod_job_id", runpod_job_id)
            except Exception as e:
                logger.warning(f"RunPod submission failed, using local worker: {e}")

        # Step 5: Poll for completion (if RunPod job ID exists)
        if runpod_job_id:
            while True:
                status = await client.get_job_status(runpod_job_id)
                state = status.get("status", "UNKNOWN")

                logger.debug(f"RunPod job {runpod_job_id} status: {state}")

                if state in ["IN_PROGRESS", "IN_QUEUE", "QUEUED"]:
                    progress_data = status.get("output", {})

                    # Normalize progress
                    progress = {
                        "percent": progress_data.get("percent", 0),
                        "stage": state,
                        "runpod_status": state,
                    }

                    update_job_field(run_id, "progress", progress)

                    if telemetry_queue:
                        try:
                            await telemetry_queue.put(
                                {
                                    "run_id": run_id,
                                    "progress": progress,
                                    "status": "running",
                                }
                            )
                        except Exception as e:
                            logger.warning(f"Telemetry queue put failed: {e}")

                    await asyncio.sleep(1.5)
                    continue

                elif state == "COMPLETED":
                    output = status.get("output", {})

                    result = {
                        "summary": "Simulation completed successfully",
                        "output": output,
                        "status": "completed",
                    }

                    update_job_field(run_id, "status", "completed")
                    update_job_field(run_id, "results", result)
                    update_job_field(
                        run_id, "completed_at", datetime.utcnow().isoformat()
                    )

                    if supabase_client:
                        try:
                            supabase_client.table("simulations").update(
                                {
                                    "status": "completed",
                                    "result_summary": result,
                                    "completed_at": datetime.utcnow().isoformat(),
                                }
                            ).eq("job_id", run_id).execute()
                            logger.info(f"Supabase updated for run_id={run_id}")
                        except Exception as e:
                            logger.error(f"Supabase update failed: {e}")

                    break

                elif state == "FAILED":
                    error_msg = status.get("output", {}).get(
                        "error", "RunPod job failed"
                    )
                    raise RuntimeError(error_msg)

                else:
                    # Unknown state, continue polling
                    await asyncio.sleep(2)
                    continue

        else:
            # Fallback: Simulate progress (dev mode without RunPod)
            num_runs = (
                payload.get("input_params", {}).get("sampling", {}).get("num_runs", 10)
            )

            for i in range(1, num_runs + 1):
                await asyncio.sleep(0.1)

                progress = {
                    "percent": int((i / num_runs) * 100),
                    "current": i,
                    "total": num_runs,
                    "stage": "processing",
                }
                update_job_field(run_id, "progress", progress)

                if telemetry_queue:
                    try:
                        await telemetry_queue.put(
                            {
                                "run_id": run_id,
                                "progress": progress,
                                "status": "running",
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Telemetry queue put failed: {e}")

            # Mark complete
            result = {
                "summary": "Simulation completed successfully",
                "runs": num_runs,
                "status": "completed",
            }

            update_job_field(run_id, "status", "completed")
            update_job_field(run_id, "results", result)
            update_job_field(run_id, "completed_at", datetime.utcnow().isoformat())

            if supabase_client:
                try:
                    supabase_client.table("simulations").update(
                        {
                            "status": "completed",
                            "result_summary": result,
                            "completed_at": datetime.utcnow().isoformat(),
                        }
                    ).eq("job_id", run_id).execute()
                except Exception as e:
                    logger.error(f"Supabase update failed: {e}")

    except Exception as e:
        logger.error(f"Pipeline failed for run_id={run_id}: {e}")

        attempt += 1
        update_job_field(run_id, "attempt", attempt)
        update_job_field(run_id, "last_error", str(e))

        # Retry logic with exponential backoff
        if attempt < MAX_ATTEMPTS and is_retryable_error(str(e)):
            backoff = BACKOFF_BASE**attempt

            update_job_field(run_id, "status", "retrying")
            logger.info(
                f"Retrying job {run_id} in {backoff}s (attempt {attempt + 1}/{MAX_ATTEMPTS})"
            )

            await asyncio.sleep(backoff)

            # Retry with same run_id (will reuse runpod_job_id if exists)
            asyncio.create_task(run_simulation_pipeline(run_id, payload, user_id))
        else:
            # Final failure
            update_job_field(run_id, "status", "failed")
            update_job_field(run_id, "error", str(e))

            if supabase_client:
                try:
                    supabase_client.table("simulations").update(
                        {"status": "failed", "error_message": str(e)}
                    ).eq("job_id", run_id).execute()
                except Exception:
                    pass

    finally:
        release_lock(run_id)


# --- Recovery Worker ---
async def recovery_worker():
    """Background worker that recovers orphaned jobs on API restart."""
    logger.info("Starting recovery worker")

    while True:
        try:
            keys = r_client.keys("job:*")

            for key in keys:
                try:
                    job = r_client.hgetall(key)

                    if not job:
                        continue

                    status = job.get("status", "")

                    # Recover running/retrying jobs that lost their worker
                    if status in ["running", "retrying"]:
                        run_id = job.get("id") or key.split(":")[-1]

                        # Avoid duplicate recovery
                        if await acquire_lock(run_id, ttl=60):
                            logger.info(f"Recovering orphaned job {run_id}")

                            payload = {
                                "scenario_name": job.get(
                                    "scenario_name", "Recovered Job"
                                ),
                                "input_params": json.loads(
                                    job.get("input_params", "{}")
                                ),
                            }

                            asyncio.create_task(
                                run_simulation_pipeline(
                                    run_id, payload, job.get("user_id", "")
                                )
                            )

                            await asyncio.sleep(1)  # Stagger recovery

                except Exception as e:
                    logger.warning(f"Error processing key {key}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Recovery worker error: {e}")

        await asyncio.sleep(10)


@router.post("/simulations", tags=["Simulations"])
async def create_simulation(
    request: RobustnessRunRequest,
    user: dict = Depends(verify_auth),
):
    """Create a new simulation and enqueue it to Redis."""
    user_id = user["user_id_internal"]
    plan = user.get("plan", UserPlan.FREE)
    limits = PLAN_LIMITS[plan]

    # 0. Check worker availability (Full Infra Registry)
    await check_compute_availability_fn()

    # 0.1 Idempotency Check (Atomic)
    # Using a temporary UUID if we need to reserve, otherwise we get existing sim_id
    temp_sim_id = str(uuid.uuid4())
    idempotency_key = (
        request.input_params.get("idempotency_key") if request.input_params else None
    )

    if idempotency_key:
        is_new = await reserve_idempotency_fn(user_id, idempotency_key, temp_sim_id)
        if not is_new:
            existing_id = await get_idempotency_value_fn(user_id, idempotency_key)
            return {
                "job_id": existing_id,
                "status": "already_exists",
                "message": "Duplicate request detected. Returning existing job ID.",
            }
        sim_id = temp_sim_id
    else:
        sim_id = temp_sim_id

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

    # Extract config from request
    config = request.config
    input_params = request.input_params or {}

    # If config provided, merge parameters into input_params
    if config:
        if config.parameters:
            input_params["parameters"] = config.parameters
        if config.sampling:
            input_params["sampling"] = config.sampling
        # Extract num_runs from sampling for scenario name
        if config.sampling and config.sampling.get("num_runs"):
            num_runs = config.sampling.get("num_runs")
            scenario_name = f"Robustness Run ({num_runs}x)"
        else:
            scenario_name = request.scenario_name or "Custom Simulation"
    else:
        scenario_name = request.scenario_name or "Custom Simulation"

    # Write to Supabase simulations table
    if supabase_client:
        try:
            supabase_client.table("simulations").insert(
                {
                    "id": sim_id,
                    "job_id": sim_id,
                    "user_id": user_id if user["type"] != "api_key" else None,
                    "status": "queued",
                    "prompt": request.prompt,
                    "input_params": input_params,
                    "scenario_name": scenario_name,
                }
            ).execute()
        except Exception as e:
            logger.error(f"Failed to insert simulation: {e}")

    # Enqueue to Redis
    job_data = {
        "id": sim_id,
        "user_id": user_id,
        "is_paid": plan != UserPlan.FREE,
        "prompt": request.prompt,
        "input_params": input_params,
        "scenario_name": scenario_name,
        "status": "queued",
        "progress": 0,
        "created_at": int(time.time()),
        "updated_at": int(time.time()),
    }

    # Patch logic: Set job detail key and push ID to queue
    r_client.set(f"job:{sim_id}", json.dumps(job_data))
    enqueue_job(sim_id)

    # Increment active jobs counter (O(1))
    increment_active_runs_fn(user_id)

    # Authority Alignment: Buffer usage event for batch flush
    add_usage_event(user_id, 1, "simulation")

    return {
        "job_id": sim_id,
        "status": "queued",
        "message": "Simulation queued. Track progress in your dashboard.",
    }


@router.get("/simulations", tags=["Simulations"])
async def list_simulations(
    limit: int = 20,
    user: dict = Depends(verify_auth),
):
    """List user's simulations from Supabase (source of truth) with Redis fallback."""
    user_id = user["user_id_internal"]
    results = []

    # Pull from Supabase (source of truth)
    if supabase_client:
        try:
            res = (
                supabase_client.table("simulations")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            if res.data:
                return {"simulations": res.data}
        except Exception as e:
            logger.error(f"Failed to fetch simulations from Supabase: {e}")

    # Fallback: Scan Redis for user's jobs
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
    return {"simulations": results[:limit]}


@router.get("/simulations/usage", tags=["Simulations"])
async def get_usage(
    user: dict = Depends(verify_auth),
):
    """Get user's weekly simulation usage."""
    user_id = user["user_id_internal"]
    usage = await get_user_usage(user_id)
    return {
        "used": usage.get("runs_used", 0),
        "limit": 10,
        "remaining": max(0, 10 - usage.get("runs_used", 0)),
    }


@router.get("/simulations/{sim_id}", tags=["Simulations"])
async def get_simulation(
    sim_id: str,
    user: dict = Depends(verify_auth),
):
    """Get a single simulation's full state."""
    job = get_job(sim_id)
    if not job:
        raise HTTPException(404, "Simulation not found")

    if job.get("user_id") != user["user_id_internal"] and user["type"] != "api_key":
        raise HTTPException(403, "Access denied")

    return job


@router.delete("/simulations/{sim_id}", tags=["Simulations"])
async def cancel_simulation(
    sim_id: str,
    user: dict = Depends(verify_auth),
):
    """Cancel a running or queued simulation."""
    job = get_job(sim_id)
    if not job:
        raise HTTPException(404, "Simulation not found")

    if job.get("user_id") != user["user_id_internal"] and user["type"] != "api_key":
        raise HTTPException(403, "Access denied")

    job["status"] = "cancelled"
    set_job(sim_id, job)

    if supabase_client:
        try:
            supabase_client.table("simulations").update({"status": "cancelled"}).eq(
                "id", sim_id
            ).execute()
        except Exception as e:
            logger.error(f"Failed to update simulation status: {e}")

    return {"simulation_id": sim_id, "status": "cancelled"}


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


@router.get("/simulations/{sim_id}/status", tags=["Simulations"])
async def get_simulation_status(
    sim_id: str,
    user: dict = Depends(verify_auth),
):
    """Get simulation status (lightweight polling endpoint)."""
    # Fetch from Redis first
    job_raw = r_client.get(f"job:{sim_id}")
    if job_raw:
        job = json.loads(job_raw)
        return {
            "job_id": sim_id,
            "status": job.get("status"),
            "progress": job.get("progress", 0),
            "created_at": job.get("created_at", ""),
            "completed_at": job.get("completed_at"),
            "error": job.get("error"),
            "result": job.get("result"),
        }

    # Fallback to Supabase if not in Redis
    if supabase_client:
        res = (
            supabase_client.table("simulations")
            .select("*")
            .eq("job_id", sim_id)
            .execute()
        )
        if res.data:
            sim = res.data[0]
            return {
                "job_id": sim_id,
                "status": sim.get("status"),
                "progress": sim.get("progress", 0),
                "created_at": sim.get("created_at", ""),
                "completed_at": sim.get("updated_at"),
                "error": sim.get("error"),
            }

    raise HTTPException(404, "Simulation not found")
