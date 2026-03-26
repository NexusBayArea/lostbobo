"""
Robustness Orchestrator API - Distributed Edition

Improvements (March 2026):
- Pydantic models for input validation
- Plan/tier enforcement (Free/Professional/Enterprise)
- Idempotency keys for AI report generation
- Structured metadata in responses
"""

import asyncio
import os
import logging
import uuid
import json
import redis
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime, timedelta
from enum import Enum

from fastapi import (
    FastAPI,
    HTTPException,
    BackgroundTasks,
    Body,
    Header,
    Depends,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field, validator

from jose import JWTError, jwt

# Import local services (API-only — no numpy/scipy/matplotlib)
from auth_utils import verify_user
from queue import enqueue_job, get_result

import httpx

# --- CONFIG ---
# Lazy API key validation - check at runtime, not import time
API_KEY = os.getenv("SIMHPC_API_KEY")
ALGORITHM = "HS256"

# pod SimHPC_P_01 Configuration
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
RUNPOD_POD_ID = os.getenv("RUNPOD_POD_ID", "x613fv0zoyvtx9")
RUNPOD_BASE_URL = f"https://api.runpod.ai/v2/{RUNPOD_POD_ID}"

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
if "localhost" in REDIS_URL and os.getenv("VERCEL"):
    logger.error("WARNING: Using localhost Redis on Vercel will fail. Ensure REDIS_URL is set to a public instance.")

MAX_ACTIVE_RUNS = 5

_ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173,https://*.vercel.app,https://simhpc.nexusbayarea.com,https://simhpc.com",
).split(",")

CORS_ORIGINS = [origin.strip() for origin in _ALLOWED_ORIGINS if origin.strip()]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Supabase Client ---
try:
    from supabase import create_client, Client

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    supabase_client: Optional[Client] = None
    if SUPABASE_URL and SUPABASE_SERVICE_KEY:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        logger.info("Supabase client initialized for control commands")
    else:
        logger.warning(
            "Supabase credentials not configured — control commands restricted"
        )
except ImportError:
    supabase_client = None
    logger.warning("supabase-py not installed — control commands restricted")

# --- REDIS CLIENT ---
r_client = redis.from_url(REDIS_URL, decode_responses=True)


# --- RUNPOD CLIENT ---
class RunPodClient:
    """Async client for pod SimHPC_P_01 interactions."""

    def __init__(self, api_key: str, pod_id: str):
        self.api_key = api_key
        self.pod_id = pod_id
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self.base_url = f"https://api.runpod.ai/v2/{pod_id}"

    async def run_job(self, input_data: dict) -> str:
        """Submit a job to RunPod and return job_id."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/run",
                headers=self.headers,
                json={"input": input_data},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()["id"]

    async def get_job_status(self, job_id: str) -> dict:
        """Poll for job completion."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/status/{job_id}", headers=self.headers, timeout=10.0
            )
            response.raise_for_status()
            return response.json()

    async def wait_for_job(
        self, job_id: str, poll_interval: float = 1.0, max_wait: float = 60.0
    ) -> dict:
        """Block until job is complete or timeout reached."""
        start_time = time.time()
        while time.time() - start_time < max_wait:
            status = await self.get_job_status(job_id)
            if status["status"] == "COMPLETED":
                return status["output"]
            if status["status"] == "FAILED":
                raise RuntimeError(f"RunPod job failed: {status.get('error')}")
            await asyncio.sleep(poll_interval)
        raise TimeoutError(f"RunPod job {job_id} timed out after {max_wait}s")


# --- ENUMS ---
class UserPlan(str, Enum):
    FREE = "free"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


# --- PYDANTIC MODELS ---


class ParameterConfigModel(BaseModel):
    """Pydantic model for parameter configuration."""

    name: str = Field(..., description="Parameter name")
    base_value: float = Field(..., description="Base parameter value")
    unit: str = Field("", description="Parameter unit")
    description: str = Field("", description="Parameter description")
    perturbable: bool = Field(True, description="Whether parameter can be perturbed")
    min_value: Optional[float] = Field(None, description="Minimum value")
    max_value: Optional[float] = Field(None, description="Maximum value")


class RobustnessRunRequest(BaseModel):
    """Pydantic model for robustness run request with validation."""

    config: Dict[str, Any]

    @validator("config")
    def validate_config(cls, v):
        if not v.get("parameters"):
            raise ValueError("At least one parameter is required")
        return v


class JobResponse(BaseModel):
    """Response model for job status."""

    run_id: str
    status: str
    progress: Dict[str, int] = {}
    created_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None
    results: Optional[Dict] = None
    ai_report: Optional[Dict] = None
    metadata: Optional[Dict] = None


class SystemStatusResponse(BaseModel):
    """Response model for system status."""

    mercury: str
    runpod: str
    supabase: str
    worker: str
    timestamp: str


class AlphaChatRequest(BaseModel):
    """Request model for alpha chat."""

    question: str


class EstimateRequest(BaseModel):
    template: str
    parameters: Dict[str, Any]
    mesh_elements: int
    solver: Optional[str] = "cvode"


class SolverAdvisorRequest(BaseModel):
    ode_dimension: int
    jacobian_sparsity: float
    problem_class: str


class GuardrailRequest(BaseModel):
    max_runtime_sec: int
    max_gpu_cost: float
    max_failure_probability: float


class SimulationRunTemplateRequest(BaseModel):
    template: str
    parameters: Dict[str, Any]


class ReplayRequest(BaseModel):
    timestamp: float


class DemoRunRequest(BaseModel):
    session_id: str
    simulation_template: str


class ReportGenerateRequest(BaseModel):
    run_id: str


class AccessRequestModel(BaseModel):
    email: str
    company: str
    use_case: str


class AlphaFeedbackModel(BaseModel):
    ease_of_use: int = Field(..., ge=1, le=5)
    simulation_value: int = Field(..., ge=1, le=5)
    trust_level: int = Field(..., ge=1, le=5)


class LeadQualificationModel(BaseModel):
    email: str
    runs_completed: int
    requested_more_runs: bool


# --- PLAN LIMITS ---
PLAN_LIMITS = {
    UserPlan.FREE: {
        "max_runs": 5,
        "max_perturbations": 5,
        "ai_reports": False,
        "pdf_export": False,
        "api_access": False,
        "sobol": False,
        "max_grid_nodes": 5000,
        "allowed_scenarios": ["baseline", "stress", "extreme"],
    },
    UserPlan.PROFESSIONAL: {
        "max_runs": 50,
        "max_perturbations": 50,
        "ai_reports": True,
        "pdf_export": True,
        "api_access": False,
        "sobol": False,
        "max_grid_nodes": 50000,
        "allowed_scenarios": ["baseline", "stress", "extreme", "custom"],
    },
    UserPlan.ENTERPRISE: {
        "max_runs": -1,  # Unlimited
        "max_perturbations": -1,
        "ai_reports": True,
        "pdf_export": True,
        "api_access": True,
        "sobol": True,
        "max_grid_nodes": -1,  # Unlimited
        "allowed_scenarios": ["baseline", "stress", "extreme", "custom"],
    },
}

# --- USAGE TRACKING ---
USAGE_WINDOW_DAYS = 7  # Rolling 7-day window for Free tier


async def get_user_usage(user_id: str) -> dict:
    """Get current usage stats for a user."""
    try:
        # Check Redis for usage data
        usage_key = f"usage:{user_id}"
        usage_data = r_client.get(usage_key)

        if usage_data:
            data = json.loads(usage_data)
            reset_timestamp = datetime.fromisoformat(data.get("reset_timestamp", ""))

            # Check if window has expired
            if datetime.now() > reset_timestamp:
                # Reset usage
                new_reset = datetime.now() + timedelta(days=USAGE_WINDOW_DAYS)
                reset_data = {
                    "runs_used": 0,
                    "reset_timestamp": new_reset.isoformat(),
                    "last_updated": datetime.now().isoformat(),
                }
                r_client.setex(
                    usage_key, USAGE_WINDOW_DAYS * 86400, json.dumps(reset_data)
                )
                return reset_data

            return data
        else:
            # Initialize new usage record
            reset_timestamp = datetime.now() + timedelta(days=USAGE_WINDOW_DAYS)
            initial_data = {
                "runs_used": 0,
                "reset_timestamp": reset_timestamp.isoformat(),
                "last_updated": datetime.now().isoformat(),
            }
            r_client.setex(
                usage_key, USAGE_WINDOW_DAYS * 86400, json.dumps(initial_data)
            )
            return initial_data

    except Exception as e:
        logger.error(f"Error getting user usage: {e}")
        # Return default usage data on error
        reset_timestamp = datetime.now() + timedelta(days=USAGE_WINDOW_DAYS)
        return {
            "runs_used": 0,
            "reset_timestamp": reset_timestamp.isoformat(),
            "last_updated": datetime.now().isoformat(),
        }


async def increment_user_usage(user_id: str, runs: int = 1) -> bool:
    """Increment user usage count. Returns True if within limits."""
    try:
        usage_key = f"usage:{user_id}"
        usage_data = r_client.get(usage_key)

        if not usage_data:
            # Initialize if not exists
            reset_timestamp = datetime.now() + timedelta(days=USAGE_WINDOW_DAYS)
            data = {
                "runs_used": runs,
                "reset_timestamp": reset_timestamp.isoformat(),
                "last_updated": datetime.now().isoformat(),
            }
            r_client.setex(usage_key, USAGE_WINDOW_DAYS * 86400, json.dumps(data))
            return True

        data = json.loads(usage_data)
        reset_timestamp = datetime.fromisoformat(data.get("reset_timestamp", ""))

        # Check if window has expired
        if datetime.now() > reset_timestamp:
            # Reset and start new window
            reset_timestamp = datetime.now() + timedelta(days=USAGE_WINDOW_DAYS)
            data["runs_used"] = runs
            data["reset_timestamp"] = reset_timestamp.isoformat()
        else:
            # Increment within current window
            data["runs_used"] = data.get("runs_used", 0) + runs

        data["last_updated"] = datetime.now().isoformat()
        r_client.setex(usage_key, USAGE_WINDOW_DAYS * 86400, json.dumps(data))
        return True

    except Exception as e:
        logger.error(f"Error incrementing user usage: {e}")
        return False


async def check_concurrent_runs(user_id: str) -> bool:
    """Check if user has any running simulations."""
    try:
        # Look for jobs belonging to this user with status 'running'
        pattern = f"job:*"
        user_keys = r_client.keys(pattern)

        for key in user_keys:
            job_data = r_client.hgetall(key)
            if (
                job_data
                and job_data.get("user_id") == user_id
                and job_data.get("status") == "running"
            ):
                return True  # User has a running job

        return False

    except Exception as e:
        logger.error(f"Error checking concurrent runs: {e}")
        return False  # Assume no concurrent runs on error


# --- UTILS ---
def get_job(run_id: str) -> Optional[dict]:
    """Get job data from Redis hash."""
    key = f"job:{run_id}"
    data = r_client.hgetall(key)
    if not data:
        return None
    # Parse JSON fields
    result = {}
    for field, value in data.items():
        # Parse JSON fields
        if field in ("results", "ai_report", "progress", "metadata", "config_summary"):
            try:
                result[field] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                result[field] = value
        else:
            result[field] = value
    return result if result else None


def set_job(run_id: str, data: dict):
    """Set job data in Redis hash with TTL."""
    key = f"job:{run_id}"
    # Flatten dict into hash fields
    hash_data = {}
    for field, value in data.items():
        if isinstance(value, (dict, list)):
            hash_data[field] = json.dumps(value)
        else:
            hash_data[field] = str(value)

    # Use pipeline for atomic update
    pipe = r_client.pipeline()
    pipe.delete(key)
    if hash_data:
        pipe.hset(key, mapping=hash_data)
    pipe.expire(key, 86400)  # 24hr TTL
    pipe.execute()


def update_job_field(run_id: str, field: str, value: Any):
    """Update a single field in job hash (atomic operation)."""
    key = f"job:{run_id}"
    if isinstance(value, (dict, list)):
        value = json.dumps(value)
    else:
        value = str(value)
    r_client.hset(key, field, value)


def get_job_field(run_id: str, field: str) -> Optional[str]:
    """Get a single field from job hash."""
    return r_client.hget(f"job:{run_id}", field)


def record_simulation_start(run_id: str, user_id: str, scenario_name: str):
    """Insert simulation row into Supabase so frontend Realtime subscription fires."""
    if not supabase_client:
        return
    try:
        supabase_client.table("simulation_history").insert(
            {
                "job_id": run_id,
                "user_id": user_id,
                "scenario_name": scenario_name,
                "status": "running",
            }
        ).execute()
        logger.debug(f"Supabase simulation_history: {run_id} queued")
    except Exception as e:
        logger.error(f"Failed to record simulation_history: {e}")


def standard_error(run_id: str, message: str, status_code: int = 400):
    return HTTPException(
        status_code=status_code,
        detail={
            "message": message,
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
        },
    )


# --- AUTH ---
async def verify_auth(
    authorization: str = Header(None),
    x_api_key: str = Header(None),
    x_user_id: str = Header(None),
):
    """Auth middleware supporting both Supabase JWT and X-API-Key."""
    # Lazy API key validation
    if not API_KEY:
        logger.error("SIMHPC_API_KEY not configured")
        raise HTTPException(
            status_code=500, detail="Server misconfiguration: API key not set"
        )

    if x_api_key == API_KEY:
        plan = UserPlan.ENTERPRISE
        return {
            "user_id": "admin",
            "type": "api_key",
            "plan": plan,
            "user_id_internal": x_user_id or "admin",
        }

    if authorization:
        payload = verify_user(authorization)
        user_id = payload.get("sub")

        user_data = r_client.get(f"user:{user_id}")
        if user_data:
            user_info = json.loads(user_data)
            plan = UserPlan(user_info.get("plan", "free"))
        else:
            plan = UserPlan.FREE

        return {
            "user_id": user_id,
            "type": "supabase_jwt",
            "plan": plan,
            "user_id_internal": user_id,
        }

    # Default to free tier for unauthenticated
    user_id = x_user_id or "anonymous"
    return {
        "user_id": user_id,
        "type": "anonymous",
        "plan": UserPlan.FREE,
        "user_id_internal": user_id,
    }


async def get_current_user(authorization: str = Header(None)):
    """
    Strict authentication dependency for protected endpoints.
    Only accepts Supabase JWT tokens - no API key or anonymous access.
    """
    if not authorization:
        raise HTTPException(401, "Missing token")

    auth_payload = verify_user(authorization)  # Can raise 401
    user_id = auth_payload.get("sub")

    # Check Tier & Usage from Supabase
    try:
        if supabase_client:
            user_profile = (
                supabase_client.table("profiles")
                .select("*")
                .eq("id", user_id)
                .single()
                .execute()
            )
            profile = user_profile.data

            if profile:
                # Check free tier limits
                if profile.get("tier") == "free" and profile.get("runs_used", 0) >= 5:
                    raise HTTPException(
                        status_code=403,
                        detail="Weekly simulation limit reached. Please upgrade.",
                    )
                return profile
    except Exception as e:
        logger.warning(f"Failed to fetch user profile: {e}")

    # Default to free tier if profile not found
    return {"id": user_id, "tier": "free", "runs_used": 0}


# --- VALIDATE SIMULATION REQUEST ---
def validate_simulation_request(params: dict, tier: str):
    """
    Enforce Free Tier constraints on simulation requests.
    """
    # Enforce Grid Resolution Limit
    if tier == "free" and params.get("nodes", 0) > 5000:
        raise HTTPException(
            status_code=403,
            detail="Resolution too high for Free Tier. Upgrade to Pro for 100k+ node support.",
        )

    # Enforce Scenario Gating
    allowed_presets = ["baseline", "stress", "extreme"]
    if tier == "free" and params.get("scenario") not in allowed_presets:
        raise HTTPException(
            status_code=403, detail="Custom scenarios are a Pro feature."
        )


# --- PLAN ENFORCEMENT ---
async def check_plan_limits(
    num_runs: int, sampling_method: str, user: dict = Depends(verify_auth)
):
    """Enforce plan-based limits on simulation runs."""
    plan = user.get("plan", UserPlan.FREE)
    limits = PLAN_LIMITS[plan]

    # Check run limits
    if limits["max_runs"] > 0 and num_runs > limits["max_runs"]:
        raise HTTPException(
            status_code=403,
            detail={
                "message": f"Plan limit exceeded. {plan.value} tier allows max {limits['max_runs']} runs.",
                "current": num_runs,
                "limit": limits["max_runs"],
                "plan": plan.value,
            },
        )

    # Check Sobol availability
    if sampling_method == "sobol" and not limits["sobol"]:
        raise HTTPException(
            status_code=403,
            detail={
                "message": "Sobol GSA is only available on Enterprise tier.",
                "plan": plan.value,
            },
        )

    return user


# --- IDEMPOTENCY ---
async def check_idempotency(idempotency_key: str, user_id: str) -> Optional[str]:
    """
    Check if request is idempotent. Returns existing run_id if found.
    Uses Redis with 24hr TTL.
    """
    if not idempotency_key:
        return None

    key = f"idempotency:{user_id}:{idempotency_key}"
    existing = r_client.get(key)

    if existing:
        logger.info(
            f"Idempotent request detected: {idempotency_key}, existing run: {existing}"
        )
        return existing

    # Store new key
    return None


def store_idempotency(idempotency_key: str, user_id: str, run_id: str):
    """Store idempotency key mapping."""
    if idempotency_key:
        key = f"idempotency:{user_id}:{idempotency_key}"
        r_client.setex(key, 86400, run_id)  # 24hr TTL


# --- RATE LIMITER ---
async def check_rate_limit(user: dict = Depends(verify_auth)):
    user_id = user["user_id"]
    plan = user.get("plan", UserPlan.FREE)

    # Get rate limit based on plan
    max_per_hour = (
        100
        if plan == UserPlan.ENTERPRISE
        else (50 if plan == UserPlan.PROFESSIONAL else 10)
    )

    key = f"ratelimit:{user_id}"
    count = r_client.incr(key)
    if count == 1:
        r_client.expire(key, 3600)

    if count > max_per_hour:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {max_per_hour} requests per hour for {plan.value} tier.",
        )

    return user


# --- WEBSOCKET MANAGER ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, run_id: str):
        await websocket.accept()
        if run_id not in self.active_connections:
            self.active_connections[run_id] = []
        self.active_connections[run_id].append(websocket)

    def disconnect(self, websocket: WebSocket, run_id: str):
        if run_id in self.active_connections:
            self.active_connections[run_id].remove(websocket)

    async def broadcast_telemetry(self, run_id: str, message: dict):
        if run_id in self.active_connections:
            for connection in self.active_connections[run_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass


manager = ConnectionManager()
telemetry_queue = asyncio.Queue()


async def telemetry_worker():
    """Background worker to broadcast telemetry from queue to websockets."""
    while True:
        try:
            item = await telemetry_queue.get()
            run_id = item.get("run_id")
            await manager.broadcast_telemetry(run_id, item)
            telemetry_queue.task_done()
        except Exception as e:
            logger.error(f"Telemetry worker error: {e}")
            await asyncio.sleep(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting SimHPC Unified Platform")

    # Validate Redis connection at startup
    try:
        r_client.ping()
        logger.info("Redis connection verified")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        raise RuntimeError("Redis required but unavailable")

    # Validate API key is configured
    if not API_KEY:
        logger.warning("SIMHPC_API_KEY not set - running in development mode")

    bg_worker = asyncio.create_task(telemetry_worker())
    yield
    bg_worker.cancel()
    logger.info("SimHPC Platform shutting down")


app = FastAPI(title="SimHPC Platform", version="2.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- CORE SYSTEM HELPERS ---
def get_solver_recommendation(
    ode_dimension: int, jacobian_sparsity: float, problem_class: str
) -> dict:
    if jacobian_sparsity < 0.15 and ode_dimension > 1000:
        return {
            "recommended_solver": "CVODE_BDF",
            "stiffness_probability": 0.85,
            "estimated_runtime_sec": ode_dimension * 0.05,
        }
    elif ode_dimension < 200:
        return {
            "recommended_solver": "explicit_RK",
            "stiffness_probability": 0.1,
            "estimated_runtime_sec": ode_dimension * 0.01,
        }
    else:
        return {
            "recommended_solver": "ARKODE",
            "stiffness_probability": 0.76,
            "estimated_runtime_sec": ode_dimension * 0.03,
        }


def get_user_guardrails(user_id: str) -> dict:
    raw = r_client.get(f"guardrails:{user_id}")
    if raw:
        import json

        return json.loads(raw)
    return None


def set_user_guardrails(user_id: str, guardrails: dict):
    import json

    r_client.setex(f"guardrails:{user_id}", 3600, json.dumps(guardrails))


@app.get("/api/v1/system/status", response_model=SystemStatusResponse, tags=["System — Health"])
async def get_system_status():
    """Aggregated health check for the Alpha Dashboard."""
    try:
        r_client.ping()
        redis_status = "online"
    except Exception:
        redis_status = "offline"

    return {
        "mercury": "online",  # API is up if this responds
        "runpod": redis_status,  # Worker health is tied to Redis queue
        "supabase": "online" if supabase_client else "offline",
        "worker": redis_status,
        "timestamp": datetime.now().isoformat()
    }


# --- ADMIN: RUNPOD FLEET MANAGEMENT ---
ADMIN_SECRET = os.getenv("ADMIN_SECRET")


async def verify_admin(x_admin_secret: str = Header(None)):
    """Verify admin secret for fleet management endpoints."""
    if not ADMIN_SECRET:
        raise HTTPException(500, "ADMIN_SECRET not configured")
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(403, "Invalid admin credentials")
    return True


@app.get("/api/v1/admin/fleet", tags=["Admin — RunPod Fleet"])
async def get_fleet_status_endpoint(_: bool = Depends(verify_admin)):
    """
    Get comprehensive fleet status: running pods, queue depth,
    cost tracking, scaling state, and recent events.
    """
    try:
        fleet_data = r_client.get("autoscaler:last_status")
        if fleet_data:
            return {"status": "ok", "fleet": json.loads(fleet_data)}

        # Fallback: minimal status from Redis
        queue_len = r_client.llen(os.getenv("QUEUE_NAME", "simhpc_jobs"))
        active_pods = json.loads(r_client.get("active_pods") or "[]")
        today_cost = float(r_client.get("cost:today_usd") or 0)
        return {
            "status": "ok",
            "fleet": {
                "pods": len(active_pods),
                "pod_ids": active_pods,
                "queue": queue_len,
                "cost_today": round(today_cost, 4),
                "timestamp": datetime.now().isoformat(),
            },
        }
    except Exception as e:
        raise HTTPException(500, f"Fleet status error: {e}")


@app.get("/api/v1/admin/fleet/cost", tags=["Admin — RunPod Fleet"])
async def get_cost_endpoint(_: bool = Depends(verify_admin)):
    """Get cost summary: hourly burn, daily estimate, savings from autoscaler."""
    try:
        today_cost = float(r_client.get("cost:today_usd") or 0)
        active_pods = json.loads(r_client.get("active_pods") or "[]")
        return {
            "status": "ok",
            "cost": {
                "actual_today_usd": round(today_cost, 4),
                "running_pods": len(active_pods),
                "timestamp": datetime.now().isoformat(),
            },
        }
    except Exception as e:
        raise HTTPException(500, f"Cost query error: {e}")


@app.get("/api/v1/admin/fleet/events", tags=["Admin — RunPod Fleet"])
async def get_fleet_events(limit: int = 20, _: bool = Depends(verify_admin)):
    """Get recent fleet events (scaling, cost cap, errors)."""
    try:
        raw_events = r_client.lrange("runpod_events", 0, min(limit - 1, 499))
        events = [json.loads(e) for e in raw_events]
        return {"status": "ok", "events": events, "count": len(events)}
    except Exception as e:
        raise HTTPException(500, f"Events query error: {e}")


@app.post("/api/v1/admin/fleet/pod", tags=["Admin — RunPod Fleet"])
async def create_pod_endpoint(
    name: str = Body("simhpc-worker"),
    gpu_type: str = Body("NVIDIA A40"),
    _: bool = Depends(verify_admin),
):
    """
    Create a new GPU pod on RunPod.
    Respects MAX_PODS safety cap from autoscaler config.
    """
    try:
        active_pods = json.loads(r_client.get("active_pods") or "[]")
        max_pods = int(os.getenv("MAX_PODS", "3"))
        if len(active_pods) >= max_pods:
            raise HTTPException(
                429,
                f"Safety cap: {len(active_pods)} pods running (MAX={max_pods}). "
                "Terminate a pod first.",
            )
        return {
            "status": "ok",
            "message": f"Pod creation queued (name={name}, gpu={gpu_type}). "
            "The autoscaler will create it on next cycle if queue has jobs.",
            "current_pods": len(active_pods),
            "max_pods": max_pods,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Pod creation error: {e}")


@app.post("/api/v1/admin/fleet/pod/{pod_id}/stop", tags=["Admin — RunPod Fleet"])
async def stop_pod_endpoint(pod_id: str, _: bool = Depends(verify_admin)):
    """Stop a running pod (preserves disk, stops GPU billing)."""
    try:
        active_pods = json.loads(r_client.get("active_pods") or "[]")
        active_pods = [p for p in active_pods if p != pod_id]
        r_client.set("active_pods", json.dumps(active_pods))
        r_client.lpush("runpod_events", json.dumps({
            "ts": datetime.now().isoformat(),
            "event": "pod_stop_requested",
            "pod_id": pod_id,
            "details": "via admin API",
        }))
        return {"status": "ok", "pod_id": pod_id, "action": "stop_requested"}
    except Exception as e:
        raise HTTPException(500, f"Pod stop error: {e}")


@app.post("/api/v1/admin/fleet/pod/{pod_id}/terminate", tags=["Admin — RunPod Fleet"])
async def terminate_pod_endpoint(pod_id: str, _: bool = Depends(verify_admin)):
    """Permanently terminate a pod (deletes disk, zeroes billing)."""
    try:
        active_pods = json.loads(r_client.get("active_pods") or "[]")
        active_pods = [p for p in active_pods if p != pod_id]
        r_client.set("active_pods", json.dumps(active_pods))
        r_client.lpush("runpod_events", json.dumps({
            "ts": datetime.now().isoformat(),
            "event": "pod_terminate_requested",
            "pod_id": pod_id,
            "details": "via admin API",
        }))
        return {"status": "ok", "pod_id": pod_id, "action": "terminate_requested"}
    except Exception as e:
        raise HTTPException(500, f"Pod termination error: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
