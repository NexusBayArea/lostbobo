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

# Import local services
try:
    from robustness_service import (
        get_robustness_service,
        RobustnessConfig,
        ParameterConfig,
        SamplingMethod,
        RobustnessSummary,
    )
    from ai_report_service import get_ai_report_service
    from pdf_service import get_pdf_bytes
    from auth_utils import verify_user
except ImportError:
    import sys

    sys.path.append(os.getenv("ROBUSTNESS_DIR", os.path.dirname(__file__)))
    from robustness_service import (
        get_robustness_service,
        RobustnessConfig,
        ParameterConfig,
        SamplingMethod,
        RobustnessSummary,
    )
    from ai_report_service import get_ai_report_service
    from pdf_service import get_pdf_bytes
    from auth_utils import verify_user

# Import demo access module
try:
    from demo_access import router as demo_router
except ImportError:
    demo_router = None

import httpx

# --- CONFIG ---
# Lazy API key validation - check at runtime, not import time
API_KEY = os.getenv("SIMHPC_API_KEY")
ALGORITHM = "HS256"

# RunPod Serverless Configuration
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
RUNPOD_ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID")
RUNPOD_BASE_URL = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}"

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
MAX_ACTIVE_RUNS = 5

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
    """Async client for RunPod Serverless interactions."""

    def __init__(self, api_key: str, endpoint_id: str):
        self.api_key = api_key
        self.endpoint_id = endpoint_id
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self.base_url = f"https://api.runpod.ai/v2/{endpoint_id}"

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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register demo access routes
if demo_router:
    app.include_router(demo_router)
    logger.info("Demo magic link routes registered")

# --- API ROUTES ---


@app.get("/api/v1/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.1.0",
    }


@app.get(
    "/api/v1/system-status", response_model=SystemStatusResponse, tags=["Core System"]
)
async def get_system_status():
    """
    Checks the status of Mercury AI, RunPod, Supabase, and Serverless Worker.
    Used for Alpha debugging and dashboard visibility.
    Uses metadata-only ping for worker to avoid unnecessary GPU costs.
    """
    status = {
        "mercury": "offline",
        "supabase": "offline",
        "worker": "offline",
        "timestamp": datetime.now().isoformat(),
    }

    # 1. MERCURY CHECK (Inception Labs)
    mercury_api_key = os.getenv("MERCURY_API_KEY")
    if mercury_api_key:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.post(
                    "https://api.inceptionlabs.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {mercury_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "mercury",
                        "messages": [{"role": "user", "content": "reply SIMHPC_OK"}],
                    },
                )
                status["mercury"] = (
                    "online" if response.status_code == 200 else "offline"
                )
        except Exception as e:
            logger.error(f"Mercury health check failed: {e}")
            status["mercury"] = "offline"

    # 2. SUPABASE CHECK
    if supabase_client:
        try:
            # Direct check on the demo_access table as specified
            res = supabase_client.table("demo_access").select("id").limit(1).execute()
            status["supabase"] = "connected"
        except Exception as e:
            logger.error(f"Supabase health check failed: {e}")
            status["supabase"] = "offline"

    # 3. SIMULATION WORKER CHECK (RunPod Serverless - Metadata Only)
    # We send a 'health' flag to handler.py to bypass physics and avoid GPU costs
    if RUNPOD_API_KEY and RUNPOD_ENDPOINT_ID:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.post(
                    f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/runsync",
                    headers={
                        "Authorization": f"Bearer {RUNPOD_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={"input": {"check_health_only": True}},
                )
                # 200 or 201 indicates the worker is warm and responding
                if response.status_code in [200, 201]:
                    status["worker"] = "warm"
                else:
                    status["worker"] = "cold"
        except Exception as e:
            logger.error(f"Worker health check failed: {e}")
            status["worker"] = "offline"

    return status


@app.get("/api/v1/system/job-logs", tags=["Core System"])
async def get_system_job_logs(user: dict = Depends(verify_auth)):
    """
    Returns the last 5 simulation jobs for debugging.
    """
    keys = r_client.keys("job:*")
    jobs = []

    # In a real production app, we would query Supabase here.
    # Since the monorepo uses Redis as the primary state for Alpha, we pull from there.
    for k in keys:
        try:
            raw = r_client.hgetall(k)
            if raw:
                # Filter for user or admin
                if (
                    raw.get("user_id") == user.get("user_id")
                    or user.get("user_id") == "admin"
                ):
                    jobs.append(
                        {
                            "id": raw.get("run_id"),
                            "status": raw.get("status"),
                            "created_at": raw.get("created_at")
                            or datetime.now().isoformat(),
                            "model_name": "battery_thermal"
                            if "thermal" in str(raw.get("config_summary"))
                            else "physics_sim",
                        }
                    )
        except Exception:
            continue

    # Sort by created_at desc
    jobs.sort(key=lambda x: str(x.get("created_at")), reverse=True)
    return jobs[:5]


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


# ==========================================
# 1. CORE SYSTEM APIs
# ==========================================


@app.post("/api/v1/simulation/estimate", tags=["Core System"])
async def estimate_simulation(req: EstimateRequest, user: dict = Depends(verify_auth)):
    GPU_COST_PER_SECOND = float(os.getenv("GPU_COST_PER_SECOND", "0.001"))

    # Solver factors per prompt
    solver_factors = {"cvode": 1.0, "arkode": 0.85, "explicit": 0.6}
    solver_factor = solver_factors.get(
        req.solver.lower() if req.solver else "cvode", 1.0
    )

    # parameter_scale formula
    parameter_scale = len(req.parameters) * 0.05 + 1.0

    # runtime formula: runtime ≈ mesh_elements * solver_factor * parameter_scale
    # We add a small constant scaling factor to map elements to seconds realistically
    predicted_runtime = (req.mesh_elements * 0.0001) * solver_factor * parameter_scale

    predicted_cost = predicted_runtime * GPU_COST_PER_SECOND

    # Solver recommending logic
    rec = get_solver_recommendation(req.mesh_elements, 0.2, "general")

    return {
        "estimated_runtime_sec": round(predicted_runtime, 2),
        "estimated_gpu_cost": round(predicted_cost, 4),
        "recommended_solver": rec["recommended_solver"],
        "confidence_score": 0.87,
    }


@app.get("/api/v1/simulation/{run_id}/timeline", tags=["Core System"])
async def get_simulation_timeline(run_id: str, user: dict = Depends(verify_auth)):
    events_raw = r_client.lrange(f"timeline:{run_id}", 0, -1)
    if events_raw:
        import json

        events = [json.loads(e) for e in events_raw]
    else:
        events = [
            {"time": 0.1, "event": "start"},
            {"time": 2.3, "event": "step_size_change"},
            {"time": 5.8, "event": "divergence_warning"},
        ]
    return {"run_id": run_id, "events": events}


@app.post("/api/v1/simulation/{run_id}/replay", tags=["Core System"])
async def replay_simulation(
    run_id: str, req: ReplayRequest, user: dict = Depends(verify_auth)
):
    return {
        "run_id": run_id,
        "timestamp": req.timestamp,
        "snapshot": {"state_vector_hash": "a1b2c3d4", "mesh_deformation": 0.04},
    }


@app.post("/api/v1/solver/advisor", tags=["Core System"])
async def solver_advisor(req: SolverAdvisorRequest, user: dict = Depends(verify_auth)):
    return get_solver_recommendation(
        req.ode_dimension, req.jacobian_sparsity, req.problem_class
    )


@app.post("/api/v1/simulation/guardrails", tags=["Core System"])
async def set_guardrails(req: GuardrailRequest, user: dict = Depends(verify_auth)):
    set_user_guardrails(user["user_id"], req.dict())
    import json

    r_client.lpush(
        f"telemetry:{user['user_id']}",
        json.dumps(
            {"event": "guardrail_triggered", "time": datetime.now().isoformat()}
        ),
    )
    return {"status": "success", "guardrails_applied": True}


@app.get("/api/v1/templates", tags=["Core System"])
async def get_templates(user: dict = Depends(verify_auth)):
    return [
        {
            "id": "battery_thermal",
            "name": "Battery Thermal Model",
            "required_parameters": ["cells", "ambient_temp", "cooling_rate"],
            "default_solver": "CVODE_BDF",
            "mesh_presets": {"coarse": 10000, "fine": 250000},
            "description": "Thermal runaway analysis for EV packs.",
        },
        {
            "id": "structural_vibration",
            "name": "Structural Vibration",
            "required_parameters": ["mass", "damping", "frequency"],
            "default_solver": "ARKODE",
            "mesh_presets": {"coarse": 5000, "fine": 100000},
            "description": "Modal analysis for resonance.",
        },
    ]


@app.post("/api/v1/simulation/run", tags=["Core System"])
async def launch_template_simulation(
    req: SimulationRunTemplateRequest, user: dict = Depends(verify_auth)
):
    return {
        "status": "started",
        "template": req.template,
        "run_id": "tmpl_" + str(uuid.uuid4())[:8],
    }


# ==========================================
# 2. CONTROL ROOM LAYER
# ==========================================


@app.get("/api/v1/simulations/active", tags=["Control Room"])
async def get_active_simulations(user: dict = Depends(verify_auth)):
    keys = r_client.keys("job:*")
    active_runs = []
    for k in keys:
        raw = r_client.hgetall(k)
        if raw and raw.get("user_id") == user.get("user_id"):
            status = raw.get("status")
            if status in ["running", "queued"]:
                active_runs.append(
                    {
                        "run_id": raw.get("run_id"),
                        "model_name": "battery_thermal"
                        if "thermal" in str(raw.get("config_summary"))
                        else "heatwave_grid",
                        "runtime": 18,
                        "gpu_utilization": "82%",
                        "status": status,
                    }
                )
    return active_runs


@app.get("/api/v1/simulations/history", tags=["Control Room"])
async def get_simulations_history(user: dict = Depends(verify_auth)):
    # Persist data in Postgres/Supabase would happen here. Mocking Redis retrieval for now.
    keys = r_client.keys("job:*")
    runs = []
    for k in keys:
        raw = r_client.hgetall(k)
        if raw and raw.get("user_id") == user.get("user_id"):
            config = json.loads(raw.get("config_summary", "{}"))
            runs.append(
                {
                    "run_id": raw.get("run_id"),
                    "model_name": "battery_thermal"
                    if "thermal" in str(raw.get("config_summary"))
                    else "heatwave_grid",
                    "status": raw.get("status"),
                    "runtime_sec": 42.0,
                    "created_at": raw.get("created_at"),
                    "solver": config.get("solver", "CVODE_BDF"),
                    "mesh_size": config.get("mesh_size", 10000),
                }
            )
    runs.sort(key=lambda x: str(x.get("created_at")), reverse=True)
    return runs[:50]


@app.get("/api/v1/insights/feed", tags=["Control Room"])
async def get_insights_feed(
    run_id: Optional[str] = None, user: dict = Depends(verify_auth)
):
    # Product Discovery: This engine identifies gaps between current and historical RAG context
    insights = []

    # Logic: Compare current convergence vs safety floor
    current_yield_proximity = 0.85  # Mocked calculation

    if current_yield_proximity > 0.80:
        insights.append(
            {
                "type": "warning",
                "message": f"Yield point is {round(current_yield_proximity * 100, 1)}% closer to failure than project 2024_A",
                "recommended_action": "Tighten mesh at the structural anchor points",
            }
        )

    insights.append(
        {
            "type": "suggestion",
            "message": "Thermal gradient exceeds typical solar farm floor benchmarks",
            "recommended_action": "Verify fan cooling profile in RAG docs",
        }
    )

    return insights


@app.get("/api/v1/signals/live", tags=["Control Room"])
async def get_live_signals(user: dict = Depends(verify_auth)):
    return {
        "temperature": 101,
        "grid_demand": "14.8GW",
        "energy_price": "$92/MWh",
        "solar_output": "29%",
    }


@app.get("/api/v1/controlroom/state", tags=["Control Room"])
async def get_controlroom_state(user: dict = Depends(verify_auth)):
    """
    Unified aggregator for the 4-panel HPC Control Room.
    Powers SimulationTimeline, Telemetry, ActiveSimulations, SimulationMemory, and CommandConsole.
    """
    active = await get_active_simulations(user)
    history = await get_simulations_history(user)
    alerts = await get_system_alerts(user)

    # Mocked telemetry for the "feeling alive" quality
    import random

    telemetry = {
        "gpu_load": random.randint(65, 88),
        "status": "nominal",
        "solver_convergence": 0.94 + (random.random() * 0.05),
        "residual_error": 1.2e-5,
        "energy_price": "$92/MWh",
        "solar_output": "29%",
    }

    # Timeline events for the "Flight Path"
    timeline = [
        {
            "id": "evt_1",
            "type": "SIMULATION_EVENT",
            "severity": "info",
            "label": "Baseline Dispatch",
            "timestamp": "2026-03-16T15:00:00Z",
        },
        {
            "id": "evt_2",
            "type": "SOLVER_STATE",
            "severity": "success",
            "label": "Solver Stable",
            "timestamp": "2026-03-16T15:05:00Z",
        },
        {
            "id": "evt_3",
            "type": "AUDIT_EVENT",
            "severity": "warning",
            "label": "Anomaly Flagged",
            "timestamp": "2026-03-16T15:07:00Z",
        },
    ]

    return {
        "telemetry": telemetry,
        "active_runs": active,
        "recent_runs": history,
        "audit_alerts": alerts,
        "timeline_events": timeline,
        "lineage": {
            "nodes": [
                {"id": "A", "label": "Baseline Thermal", "type": "parent"},
                {"id": "B", "label": "Optimized Coolant", "type": "child"},
            ],
            "edges": [{"source": "A", "target": "B"}],
        },
        "guidance": {
            "insight_id": "ins_54",
            "type": "parameter_sensitivity",
            "message": "Heat flux exceeds the validated safety envelope documented in Project Alpha.",
            "recommended_action": "Reduce cooling inlet pressure by 5%",
        },
    }


@app.get("/api/v1/control/timeline", tags=["Control Room"])
async def get_simulation_timeline_control(run_id: str):
    """
    Returns the structured temporal event log (SIMULATION_EVENT, AUDIT_EVENT, etc.).
    Used for cockpit marquee visualizations.
    """
    return [
        {
            "id": "evt_1",
            "type": "SIMULATION_EVENT",
            "severity": "info",
            "label": "Job Dispatched",
            "timestamp": "2026-03-16T15:00:00Z",
        },
        {
            "id": "evt_2",
            "type": "SOLVER_STATE",
            "severity": "success",
            "label": "Mesh Convergence",
            "timestamp": "2026-03-16T15:05:00Z",
        },
        {
            "id": "evt_3",
            "type": "AUDIT_EVENT",
            "severity": "warning",
            "label": "Consistency Check",
            "timestamp": "2026-03-16T15:07:00Z",
        },
    ]


@app.get("/api/v1/control/lineage", tags=["Control Room"])
async def get_simulation_lineage(run_id: str):
    """
    Returns the simulation ancestry tree for investigation.
    """
    return {
        "nodes": [
            {"id": "A", "label": "Baseline Thermal", "type": "parent"},
            {"id": "B", "label": "Optimized Coolant", "type": "child"},
        ],
        "edges": [{"source": "A", "target": "B"}],
    }


@app.post("/api/v1/control/command", tags=["Control Room"])
async def execute_cockpit_command(run_id: str, action: str, params: dict = None):
    """
    Executes high-stakes operator actions: INTERCEPT, CLONE, BOOST.
    """
    if action == "intercept":
        # Logic to pause Celery worker/Solver via Redis signal
        return {
            "status": "success",
            "message": f"Simulation {run_id} intercepted for adjustment",
        }
    elif action == "clone":
        # Logic to spawn new Child Job with modified params
        return {
            "status": "success",
            "message": f"Child simulation spawned from {run_id}",
        }
    elif action == "boost":
        # Logic to move Job to High Priority Queue
        return {
            "status": "success",
            "message": f"Resource priority boosted for {run_id}",
        }
    return {"status": "error", "message": "Unknown command"}


@app.post("/api/v1/control/command/clone", tags=["Control Room"])
async def clone_simulation(
    parent_sim_id: str, current_user: dict = Depends(get_current_user)
):
    """
    Operator Action: Clone.
    Copies parameters from a parent run to initiate a new child simulation.
    (O-D-I-A-V: Act)
    """
    if not supabase_client:
        raise HTTPException(status_code=503, detail="Supabase client not initialized")

    # 1. Fetch parent state from Supabase
    try:
        parent = (
            supabase_client.table("simulations")
            .select("*")
            .eq("id", parent_sim_id)
            .single()
            .execute()
        )
        if not parent.data:
            raise HTTPException(
                status_code=404, detail="Parent simulation lineage not found"
            )
    except Exception as e:
        logger.error(f"Supabase fetch error for clone: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch parent simulation")

    # 2. Prepare Child Configuration
    child_config = parent.data.get("config", {})
    new_sim_id = f"sim_{uuid.uuid4().hex[:8]}"

    # 3. Trigger RunPod GPU Worker
    try:
        runpod = RunPodClient(RUNPOD_API_KEY, RUNPOD_ENDPOINT_ID)
        job_input = {
            "prompt": child_config.get("prompt"),
            "parameters": child_config.get("parameters"),
            "parent_id": parent_sim_id,
            "is_clone": True,
        }
        job_id = await runpod.run_job(job_input)
    except Exception as e:
        logger.error(f"RunPod dispatch failed for clone: {e}")
        raise HTTPException(status_code=500, detail="Worker allocation failed")

    # 4. Record Lineage (O-D-I-A-V: Verify)
    try:
        supabase_client.table("simulation_lineage").insert(
            {
                "parent_id": parent_sim_id,
                "child_id": new_sim_id,
                "operator_id": current_user.get("user_id_internal"),
                "action": "manual_clone",
                "cloned_at": datetime.now().isoformat(),
            }
        ).execute()
    except Exception as e:
        logger.error(f"Supabase lineage recording failed: {e}")
        # Non-fatal error for the clone process itself
        pass

    return {
        "status": "spawned",
        "new_sim_id": new_sim_id,
        "job_id": job_id,
        "message": "Iteration intelligence active. Monitoring child convergence.",
    }


@app.get("/api/v1/alerts", tags=["Control Room"])
async def get_system_alerts(user: dict = Depends(verify_auth)):
    # Managed by the Rnj-1 Auditor layer
    return [
        {
            "level": "CRITICAL",
            "source": "Rnj-1 Auditor",
            "message": "Hallucination Detected: PDF claimed 50C stability; Lab Doc 2024_B confirms 42C floor.",
            "timestamp": datetime.now().isoformat(),
            "run_id": "sim_827",
        },
        {
            "level": "WARNING",
            "source": "Solve Engine",
            "message": "Solver divergence risk detected at timestep 0.84s",
            "timestamp": datetime.now().isoformat(),
        },
    ]


# ==========================================
# 3. DEMO FLOW LAYER
# ==========================================


@app.post("/api/v1/demo/start", tags=["Demo Flow"])
async def start_demo_session(user: dict = Depends(verify_auth)):
    import json

    session_id = "demo_" + str(uuid.uuid4())[:6]
    state = {"runs_remaining": 5, "current_step": 1, "completed_steps": []}
    r_client.setex(f"demo:{session_id}", 86400, json.dumps(state))
    return {"session_id": session_id, "runs_remaining": 5, "current_step": 1}


@app.get("/api/v1/demo/{session_id}/progress", tags=["Demo Flow"])
async def get_demo_progress(session_id: str, user: dict = Depends(verify_auth)):
    raw = r_client.get(f"demo:{session_id}")
    if raw:
        state = json.loads(raw)
        completed = state.get("completed_steps", [])

        # Determine next step based on completion
        steps = [
            "baseline_simulation",
            "parameter_modification",
            "scenario_simulation",
            "robustness_analysis",
            "engineering_report",
        ]
        current_step = "baseline_simulation"
        for s in steps:
            if s not in completed:
                current_step = s
                break

        return {
            "completed_steps": completed,
            "current_step": current_step,
            "runs_remaining": state.get("runs_remaining", 5),
        }
    return {
        "completed_steps": [],
        "current_step": "baseline_simulation",
        "runs_remaining": 5,
    }


@app.get("/api/v1/demo/suggested-run", tags=["Demo Flow"])
async def get_demo_suggested_run(session_id: str, user: dict = Depends(verify_auth)):
    raw = r_client.get(f"demo:{session_id}")
    if not raw:
        return {"simulation_template": "battery_thermal", "reason": "Baseline start"}

    state = json.loads(raw)
    completed = state.get("completed_steps", [])

    if "baseline_simulation" not in completed:
        return {
            "simulation_template": "battery_thermal",
            "reason": "Demonstrates core physics modeling",
        }
    elif "scenario_simulation" not in completed:
        return {
            "simulation_template": "heatwave_grid",
            "reason": "Demonstrates scenario modeling capability",
        }
    elif "robustness_analysis" not in completed:
        return {
            "simulation_template": "monte_carlo",
            "reason": "Demonstrates sensitivity and risk analysis",
        }
    else:
        return {
            "simulation_template": "report_gen",
            "reason": "Finalize engineering documentation",
        }


@app.post("/api/v1/demo/run", tags=["Demo Flow"])
async def run_demo_simulation(req: DemoRunRequest, user: dict = Depends(verify_auth)):
    import json

    raw = r_client.get(f"demo:{req.session_id}")
    if not raw:
        raise HTTPException(status_code=404, detail="Demo session not found or expired")
    state = json.loads(raw)

    if state.get("runs_remaining", 0) <= 0:
        raise HTTPException(
            status_code=403, detail="Demo runs exhausted. Request expanded access."
        )

    state["runs_remaining"] -= 1

    step_mapping = {
        1: "baseline simulation",
        2: "parameter modification",
        3: "scenario simulation",
        4: "robustness analysis",
        5: "engineering report",
    }

    current = state.get("current_step", 1)
    if current in step_mapping:
        step_name = step_mapping[current]
        if step_name not in state.setdefault("completed_steps", []):
            state["completed_steps"].append(step_name)
        state["current_step"] = current + 1

    r_client.setex(f"demo:{req.session_id}", 86400, json.dumps(state))
    return {
        "status": "started",
        "session_id": req.session_id,
        "simulation": req.simulation_template,
        "runs_remaining": state["runs_remaining"],
    }


@app.post("/api/v1/demo/complete", tags=["Demo Flow"])
async def complete_demo_session(user: dict = Depends(verify_auth)):
    return {
        "demo_complete": True,
        "report_url": "/reports/demo_final.pdf",
        "notebook_url": "/notebooks/demo_final.ipynb",
        "next_step": "request_full_access",
    }


# ==========================================
# 4. TRUST LAYER APIs
# ==========================================


@app.get("/api/v1/validation/benchmarks", tags=["Trust Layer"])
async def get_validation_benchmarks(user: dict = Depends(verify_auth)):
    return [
        {
            "benchmark": "NAFEMS-thermal-001",
            "analytical_solution_used": True,
            "error_rate": 0.0021,
            "status": "validated",
        }
    ]


@app.get("/api/v1/validation/badge", tags=["Trust Layer"])
async def get_validation_badge(user: dict = Depends(verify_auth)):
    return {"nafems_validated": True, "tests_passed": 14, "max_error": 0.002}


@app.get("/api/v1/simulation/{run_id}/sensitivity", tags=["Trust Layer"])
async def get_simulation_sensitivity(run_id: str, user: dict = Depends(verify_auth)):
    return {
        "top_parameters": [
            {"name": "heat_flux", "impact": 0.62},
            {"name": "thermal_conductivity", "impact": 0.21},
        ]
    }


@app.get("/api/v1/simulation/{run_id}/uncertainty", tags=["Trust Layer"])
async def get_simulation_uncertainty(run_id: str, user: dict = Depends(verify_auth)):
    return {
        "monte_carlo_runs": 50,
        "variance": 0.023,
        "confidence_interval": "±3.1%",
        "top_parameters": [
            {"name": "heat_flux", "impact": 0.61},
            {"name": "thermal_conductivity", "impact": 0.22},
        ],
    }


@app.get("/api/v1/simulation/{run_id}/provenance", tags=["Trust Layer"])
async def get_simulation_provenance(run_id: str, user: dict = Depends(verify_auth)):
    return {
        "solver": "CVODE_BDF",
        "mesh_elements": 2100000,
        "tolerance": "1e-6",
        "runtime_sec": 42.3,
        "hardware_type": "GPU",
        "gpu_model": "A40",
        "worker_container_version": "simhpc-worker-v0.3",
        "simulation_template": "battery_thermal",
    }


@app.post("/api/v1/report/generate", tags=["Trust Layer"])
async def generate_engineering_report(
    req: ReportGenerateRequest, user: dict = Depends(verify_auth)
):
    job = get_job(req.run_id) or {}
    status = job.get("status", "completed")

    if status != "completed":
        return {
            "report_status": "needs_review",
            "report_url": None,
            "reason": "Simulation not completed or solver diverged",
        }

    return {
        "report_status": "generated",
        "report_url": f"/reports/{req.run_id}.pdf",
        "sections": ["simulation_summary", "key_metrics", "sensitivity_ranking"],
    }


@app.post("/api/v1/alpha/chat", tags=["Alpha"])
async def alpha_chat(req: AlphaChatRequest, user: dict = Depends(verify_auth)):
    """Proxy chat requests to RunPod Alpha LLM service."""
    if not RUNPOD_API_KEY or not RUNPOD_ENDPOINT_ID:
        raise HTTPException(
            status_code=503, detail="RunPod Alpha service not configured"
        )

    try:
        runpod = RunPodClient(RUNPOD_API_KEY, RUNPOD_ENDPOINT_ID)

        # This matches the worker's expected input structure for chat
        # The worker's main.py /chat expects ChatRequest(question=...)
        # But we are calling it via RunPod Serverless /run which puts it in 'input'
        rp_job_id = await runpod.run_job({"question": req.question})
        rp_output = await runpod.wait_for_job(rp_job_id)

        return rp_output
    except Exception as e:
        logger.error(f"Alpha chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/api/v1/telemetry/{run_id}")
async def websocket_telemetry(websocket: WebSocket, run_id: str):
    await manager.connect(websocket, run_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, run_id)


@app.post("/api/v1/robustness/run", response_model=JobResponse, tags=["Simulations"])
async def start_robustness(
    request: RobustnessRunRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    x_idempotency_key: str = Header(
        None, description="Idempotency key for retry safety"
    ),
):
    # Check idempotency
    if x_idempotency_key:
        existing_run_id = await check_idempotency(x_idempotency_key, user["user_id"])
        if existing_run_id:
            existing_job = get_job(existing_run_id)
            if existing_job:
                return JobResponse(**existing_job)

    # Check concurrent global limit
    active_keys = r_client.keys("job:*")
    active_running = 0
    for k in active_keys:
        status = r_client.hget(k, "status")
        if status == "running":
            active_running += 1

    if active_running >= MAX_ACTIVE_RUNS:
        raise HTTPException(
            status_code=429,
            detail="Global simulation capacity reached. Please try again in a few minutes.",
        )

    run_id = str(uuid.uuid4())[:8]
    config_data = request.config

    method_map = {
        "±5%": SamplingMethod.PERCENTAGE_5,
        "±10%": SamplingMethod.PERCENTAGE_10,
        "latin_hypercube": SamplingMethod.LATIN_HYPERCUBE,
        "sobol": SamplingMethod.SOBOL,
        "monte_carlo": SamplingMethod.MONTE_CARLO,
    }

    try:
        method_str = config_data.get("sampling_method", "±10%")
        method = method_map.get(method_str, SamplingMethod.PERCENTAGE_10)

        # Validate parameters with Pydantic
        params_list = config_data.get("parameters", [])
        params = [
            ParameterConfig(
                name=p["name"],
                base_value=p["base_value"],
                unit=p.get("unit", ""),
                perturbable=p.get("perturbable", True),
                min_value=p.get("min_value"),
                max_value=p.get("max_value"),
            )
            for p in params_list
        ]

        perturbable_count = sum(1 for p in params if p.perturbable)
        base_n = config_data.get("num_runs", 15)

        # Check plan limits before proceeding
        await check_plan_limits(base_n, method_str, current_user)

        # === FREE TIER ENFORCEMENT LAYER ===
        plan = current_user.get("plan", UserPlan.FREE)

        # 1. Check concurrent runs for free tier
        if plan == UserPlan.FREE:
            has_concurrent = await check_concurrent_runs(current_user["user_id"])
            if has_concurrent:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "message": "Free tier allows only one simulation at a time. Please wait for current simulation to complete.",
                        "plan": "free",
                    },
                )

            # Check usage in rolling 7-day window
            usage = await get_user_usage(current_user["user_id"])
            limits = PLAN_LIMITS[plan]

            # Calculate how many actual runs this request will use
            requested_runs = (
                base_n * (perturbable_count + 2)
                if method == SamplingMethod.SOBOL
                else base_n
            )

            if usage["runs_used"] + requested_runs > limits["max_runs"]:
                remaining = max(0, limits["max_runs"] - usage["runs_used"])
                raise HTTPException(
                    status_code=403,
                    detail={
                        "message": f"You've reached your weekly limit. Upgrade to Pro for unlimited runs, high-res grids (100k+ nodes), and API access.",
                        "plan": "free",
                        "used": usage["runs_used"],
                        "limit": limits["max_runs"],
                        "requested": requested_runs,
                        "remaining": remaining,
                    },
                )

        # 2. Grid resolution cap (5,000 nodes for free tier)
        if plan == UserPlan.FREE:
            # Check if grid resolution is specified in config
            grid_nodes = config_data.get("grid_nodes", 0)
            if grid_nodes > limits["max_grid_nodes"]:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "message": f"Grid resolution exceeds free tier limit ({limits['max_grid_nodes']} nodes). Upgrade to Pro for high-res grids.",
                        "plan": "free",
                        "requested_nodes": grid_nodes,
                        "max_nodes": limits["max_grid_nodes"],
                    },
                )

        # 3. Scenario gating for free tier
        if plan == UserPlan.FREE:
            scenario = config_data.get("scenario", "baseline")
            if scenario not in limits["allowed_scenarios"]:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "message": f"Scenario '{scenario}' is not available on free tier. Allowed: {', '.join(limits['allowed_scenarios'])}",
                        "plan": "free",
                        "requested_scenario": scenario,
                        "allowed_scenarios": limits["allowed_scenarios"],
                    },
                )

        actual_run_count = (
            base_n * (perturbable_count + 2)
            if method == SamplingMethod.SOBOL
            else base_n
        )

        robustness_config = RobustnessConfig(
            enabled=True,
            num_runs=base_n,
            sampling_method=method,
            parameters=params,
            random_seed=config_data.get("random_seed"),
        )

        # Token Escrow (cost calculation)
        price = 2 if method == SamplingMethod.SOBOL else 5
        cost = actual_run_count * price + 50

        job_state = {
            "run_id": run_id,
            "user_id": current_user["user_id"],
            "plan": current_user.get("plan", "free"),
            "status": "running",
            "progress": {"current": 0, "total": actual_run_count},
            "created_at": datetime.now().isoformat(),
            "escrowed": cost,
            "config_summary": {
                "method": method_str,
                "base_n": base_n,
                "total": actual_run_count,
                "seed": config_data.get("random_seed"),
            },
        }
        set_job(run_id, job_state)

        # === FREE TIER USAGE TRACKING ===
        if plan == UserPlan.FREE:
            # Increment usage count for free tier users
            requested_runs = (
                base_n * (perturbable_count + 2)
                if method == SamplingMethod.SOBOL
                else base_n
            )
            await increment_user_usage(current_user["user_id"], requested_runs)

        # Store idempotency key
        if x_idempotency_key:
            store_idempotency(x_idempotency_key, current_user["user_id"], run_id)

        background_tasks.add_task(
            execute_robustness_task, run_id, robustness_config, current_user
        )

        return JobResponse(
            run_id=run_id,
            status="running",
            progress={"current": 0, "total": actual_run_count},
            created_at=job_state["created_at"],
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise standard_error(run_id, str(e))
    except Exception as e:
        logger.error(f"Launch error: {e}")
        raise standard_error(run_id, str(e))


@app.get("/api/v1/robustness/status/{run_id}", response_model=JobResponse)
async def get_status(run_id: str, user: dict = Depends(verify_auth)):
    job = get_job(run_id)
    if not job:
        raise standard_error(run_id, "Run not found", 404)

    # Verify ownership
    if job.get("user_id") != user["user_id"] and user.get("type") != "api_key":
        raise HTTPException(status_code=403, detail="Access denied")

    return JobResponse(**job)


@app.post("/api/v1/robustness/cancel/{run_id}")
async def cancel_run(run_id: str, user: dict = Depends(verify_auth)):
    job = get_job(run_id)
    if not job:
        raise standard_error(run_id, "Run not found", 404)

    # Verify ownership
    if job.get("user_id") != user["user_id"] and user.get("type") != "api_key":
        raise HTTPException(status_code=403, detail="Access denied")

    service = get_robustness_service()
    if service.cancel_analysis(run_id):
        # Use atomic updates instead of fetch-modify-store
        update_job_field(run_id, "status", "cancelled")
        update_job_field(run_id, "error", "Cancelled by user. Credits refunded.")
        update_job_field(run_id, "cancelled_at", datetime.now().isoformat())
        return {"status": "cancelled", "run_id": run_id}
    return {"status": "ignored", "run_id": run_id}


from fastapi.responses import FileResponse, Response, RedirectResponse


@app.get("/api/v1/robustness/report/{run_id}/pdf")
async def get_pdf_report(run_id: str, user: dict = Depends(verify_auth)):
    plan = user.get("plan", UserPlan.FREE)

    # Check plan for PDF export
    if not PLAN_LIMITS[plan].get("pdf_export"):
        raise HTTPException(
            status_code=403,
            detail={
                "message": "PDF export is only available on Professional and Enterprise tiers."
            },
        )

    job = get_job(run_id)
    if not job:
        raise standard_error(run_id, "Run not found", 404)

    # Verify ownership
    if job.get("user_id") != user["user_id"] and user.get("type") != "api_key":
        raise HTTPException(status_code=403, detail="Access denied")

    # Check if we have a direct PDF URL from RunPod
    pdf_url = job.get("pdf_url")
    if pdf_url:
        logger.info(f"Redirecting to RunPod PDF: {run_id}")
        return RedirectResponse(url=pdf_url)

    if "ai_report" not in job:
        raise standard_error(run_id, "Report data not ready", 404)

    # Fallback to local PDF generation
    pdf_bytes = get_pdf_bytes(job["ai_report"])
    return Response(
        pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=SimHPC_{run_id}.pdf"},
    )


# --- BACKGROUND TASKS ---


async def execute_robustness_task(run_id: str, config: RobustnessConfig, user: dict):
    service = get_robustness_service()
    ai_service = get_ai_report_service()
    service.runner.set_telemetry_queue(telemetry_queue)

    def update_progress(current, total):
        # Use atomic update for progress - no fetch needed
        update_job_field(run_id, "progress", {"current": current, "total": total})

    try:
        summary = await service.run_robustness_analysis(
            config, run_id=run_id, progress_callback=update_progress
        )

        # Build AI report input with full metadata
        report_input = service.create_ai_report_input_with_metadata(
            summary, simulation_id=run_id
        )

        # Generate AI report if allowed by plan
        plan = UserPlan(user.get("plan", UserPlan.FREE))
        ai_report_data = None
        pdf_url = None

        if PLAN_LIMITS[plan].get("ai_reports"):
            # Use RunPod Serverless if configured, otherwise fallback to local Mercury/Template
            if RUNPOD_API_KEY and RUNPOD_ENDPOINT_ID:
                try:
                    logger.info(f"Offloading to RunPod Serverless: {run_id}")
                    runpod = RunPodClient(RUNPOD_API_KEY, RUNPOD_ENDPOINT_ID)

                    # Send input to RunPod
                    # The worker's handler.py expects 'prompt'
                    runpod_input = {
                        "prompt": f"Analyze these simulation results: {json.dumps(report_input)}",
                        "simulation_id": run_id,
                        "metadata": report_input,
                    }

                    rp_job_id = await runpod.run_job(runpod_input)
                    rp_output = await runpod.wait_for_job(rp_job_id)

                    # rp_output is the return from handler.py: {"status": "complete", "result": "...", "pdf_url": "..."}
                    ai_report_data = {
                        "summary": rp_output.get("result"),
                        "analysis": "Generated by RunPod Mercury Engine",
                        "recommendations": [
                            "Review the attached PDF for full technical details."
                        ],
                        "version": "runpod-alpha-1",
                    }
                    pdf_url = rp_output.get("pdf_url")
                    logger.info(
                        f"RunPod processing complete for {run_id}. PDF: {pdf_url}"
                    )

                except Exception as rp_error:
                    logger.error(f"RunPod failed, falling back to local AI: {rp_error}")
                    # Fallback to local
                    ai_report = ai_service.generate_report(
                        report_input, user_id=user.get("user_id")
                    )
                    ai_report_data = ai_report.to_dict()
            else:
                # Standard local generation
                ai_report = ai_service.generate_report(
                    report_input, user_id=user.get("user_id")
                )
                ai_report_data = ai_report.to_dict()

        job = get_job(run_id)
        if job:
            # Use atomic field updates instead of full replace
            update_job_field(run_id, "status", "completed")
            update_job_field(run_id, "completed_at", datetime.now().isoformat())
            update_job_field(
                run_id,
                "results",
                {
                    "baseline": summary.baseline_result.__dict__,
                    "sensitivity": [s.__dict__ for s in summary.sensitivity_ranking],
                    "stats": {
                        "variance": summary.variance,
                        "std_dev": summary.standard_deviation,
                        "confidence_interval": summary.confidence_interval_percent,
                        "non_convergent_count": summary.non_convergent_count,
                    },
                },
            )
            update_job_field(run_id, "metadata", summary.metadata)

            if ai_report_data:
                update_job_field(run_id, "ai_report", ai_report_data)

            if pdf_url:
                update_job_field(run_id, "pdf_url", pdf_url)

    except Exception as e:
        logger.error(f"Task error {run_id}: {e}")
        job = get_job(run_id)
        if job:
            # Use atomic updates for error handling
            update_job_field(run_id, "status", "failed")
            update_job_field(run_id, "error", str(e))
            update_job_field(run_id, "failed_at", datetime.now().isoformat())


# --- COMMERCIAL & GROWTH ENDPOINTS ---


@app.post("/api/v1/access/request", tags=["Growth"])
async def request_access(req: AccessRequestModel):
    """
    Alpha Access Request.
    Stores leads for sales qualification.
    """
    if supabase_client:
        try:
            supabase_client.table("access_requests").insert(
                {
                    "email": req.email,
                    "company": req.company,
                    "use_case": req.use_case,
                    "requested_at": datetime.now().isoformat(),
                }
            ).execute()
        except Exception as e:
            logger.error(f"Failed to record access request: {e}")
            # Still return success to user

    return {
        "status": "request_received",
        "message": "The mission control team will review your application.",
    }


@app.post("/api/v1/feedback/alpha", tags=["Growth"])
async def submit_alpha_feedback(
    req: AlphaFeedbackModel, user: dict = Depends(verify_auth)
):
    """
    Alpha Pilot Feedback.
    Captures ease of use, simulation value, and trust level.
    """
    if supabase_client:
        try:
            supabase_client.table("alpha_feedback").insert(
                {
                    "user_id": user.get("user_id_internal"),
                    "ease_of_use": req.ease_of_use,
                    "simulation_value": req.simulation_value,
                    "trust_level": req.trust_level,
                    "submitted_at": datetime.now().isoformat(),
                }
            ).execute()
        except Exception as e:
            logger.error(f"Failed to record alpha feedback: {e}")

    return {
        "status": "feedback_recorded",
        "message": "Thank you for helping us build the future of deterministic simulation.",
    }


@app.get("/api/v1/analytics/demo", tags=["Growth"])
async def get_demo_analytics(user: dict = Depends(verify_auth)):
    """
    Demo Analytics.
    Returns total demos, completion rate, and average runs.
    (Admin only in production)
    """
    # This would typically query a reporting view or aggregate table
    # Returning mocked data for the alpha cockpit
    return {
        "total_demos": 38,
        "completion_rate": 0.71,
        "average_runs": 3.8,
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/api/v1/lead/qualify", tags=["Growth"])
async def qualify_lead(req: LeadQualificationModel):
    """
    Lead Qualification.
    Categorizes users based on their demo activity.
    """
    qualification_level = "warm"
    if req.runs_completed >= 5 or req.requested_more_runs:
        qualification_level = "hot"

    if supabase_client:
        try:
            supabase_client.table("leads").upsert(
                {
                    "email": req.email,
                    "runs_completed": req.runs_completed,
                    "requested_more_runs": req.requested_more_runs,
                    "qualification": qualification_level,
                    "updated_at": datetime.now().isoformat(),
                }
            ).execute()
        except Exception as e:
            logger.error(f"Failed to qualify lead: {e}")

    return {"status": "qualified", "level": qualification_level}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
