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
from datetime import datetime
from enum import Enum

from fastapi import FastAPI, HTTPException, BackgroundTasks, Body, Header, Depends, WebSocket, WebSocketDisconnect
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
        RobustnessSummary
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
        RobustnessSummary
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
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "your-supabase-jwt-secret-placeholder")
ALGORITHM = "HS256"

# RunPod Serverless Configuration
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
RUNPOD_ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID")
RUNPOD_BASE_URL = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}"

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
MAX_ACTIVE_RUNS = 5

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            "Content-Type": "application/json"
        }
        self.base_url = f"https://api.runpod.ai/v2/{endpoint_id}"

    async def run_job(self, input_data: dict) -> str:
        """Submit a job to RunPod and return job_id."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/run",
                headers=self.headers,
                json={"input": input_data},
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()["id"]

    async def get_job_status(self, job_id: str) -> dict:
        """Poll for job completion."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/status/{job_id}",
                headers=self.headers,
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()

    async def wait_for_job(self, job_id: str, poll_interval: float = 1.0, max_wait: float = 60.0) -> dict:
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
    
    @validator('config')
    def validate_config(cls, v):
        if not v.get('parameters'):
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


class AlphaChatRequest(BaseModel):
    """Request model for alpha chat."""
    question: str


# --- PLAN LIMITS ---
PLAN_LIMITS = {
    UserPlan.FREE: {
        "max_runs": 5,
        "max_perturbations": 5,
        "ai_reports": False,
        "pdf_export": False,
        "api_access": False,
        "sobol": False
    },
    UserPlan.PROFESSIONAL: {
        "max_runs": 50,
        "max_perturbations": 50,
        "ai_reports": True,
        "pdf_export": True,
        "api_access": False,
        "sobol": False
    },
    UserPlan.ENTERPRISE: {
        "max_runs": -1,  # Unlimited
        "max_perturbations": -1,
        "ai_reports": True,
        "pdf_export": True,
        "api_access": True,
        "sobol": True
    }
}

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
        if field in ('results', 'ai_report', 'progress', 'metadata', 'config_summary'):
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
        detail={"message": message, "run_id": run_id, "timestamp": datetime.now().isoformat()}
    )

# --- AUTH ---
async def verify_auth(
    authorization: str = Header(None), 
    x_api_key: str = Header(None),
    x_user_id: str = Header(None)
):
    """Auth middleware supporting both Supabase JWT and X-API-Key."""
    # Lazy API key validation
    if not API_KEY:
        logger.error("SIMHPC_API_KEY not configured")
        raise HTTPException(status_code=500, detail="Server misconfiguration: API key not set")
    
    if x_api_key == API_KEY:
        plan = UserPlan.ENTERPRISE
        return {"user_id": "admin", "type": "api_key", "plan": plan, "user_id_internal": x_user_id or "admin"}
    
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
            "user_id_internal": user_id
        }
    
    # Default to free tier for unauthenticated
    user_id = x_user_id or "anonymous"
    return {"user_id": user_id, "type": "anonymous", "plan": UserPlan.FREE, "user_id_internal": user_id}

# --- PLAN ENFORCEMENT ---
async def check_plan_limits(
    num_runs: int,
    sampling_method: str,
    user: dict = Depends(verify_auth)
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
                "plan": plan.value
            }
        )
    
    # Check Sobol availability
    if sampling_method == "sobol" and not limits["sobol"]:
        raise HTTPException(
            status_code=403,
            detail={
                "message": "Sobol GSA is only available on Enterprise tier.",
                "plan": plan.value
            }
        )
    
    return user


# --- IDEMPOTENCY ---
async def check_idempotency(
    idempotency_key: str,
    user_id: str
) -> Optional[str]:
    """
    Check if request is idempotent. Returns existing run_id if found.
    Uses Redis with 24hr TTL.
    """
    if not idempotency_key:
        return None
    
    key = f"idempotency:{user_id}:{idempotency_key}"
    existing = r_client.get(key)
    
    if existing:
        logger.info(f"Idempotent request detected: {idempotency_key}, existing run: {existing}")
        return existing
    
    # Store new key
    return None


def store_idempotency(
    idempotency_key: str,
    user_id: str,
    run_id: str
):
    """Store idempotency key mapping."""
    if idempotency_key:
        key = f"idempotency:{user_id}:{idempotency_key}"
        r_client.setex(key, 86400, run_id)  # 24hr TTL


# --- RATE LIMITER ---
async def check_rate_limit(user: dict = Depends(verify_auth)):
    user_id = user["user_id"]
    plan = user.get("plan", UserPlan.FREE)
    
    # Get rate limit based on plan
    max_per_hour = 100 if plan == UserPlan.ENTERPRISE else (50 if plan == UserPlan.PROFESSIONAL else 10)
    
    key = f"ratelimit:{user_id}"
    count = r_client.incr(key)
    if count == 1:
        r_client.expire(key, 3600)
    
    if count > max_per_hour:
        raise HTTPException(
            status_code=429, 
            detail=f"Rate limit exceeded. Max {max_per_hour} requests per hour for {plan.value} tier."
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
        "version": "2.1.0"
    }

@app.post("/api/v1/alpha/chat", tags=["Alpha"])
async def alpha_chat(
    req: AlphaChatRequest,
    user: dict = Depends(verify_auth)
):
    """Proxy chat requests to RunPod Alpha LLM service."""
    if not RUNPOD_API_KEY or not RUNPOD_ENDPOINT_ID:
        raise HTTPException(status_code=503, detail="RunPod Alpha service not configured")

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
    user: dict = Depends(check_rate_limit),
    x_idempotency_key: str = Header(None, description="Idempotency key for retry safety")
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
        raise HTTPException(status_code=429, detail="Global simulation capacity reached. Please try again in a few minutes.")

    run_id = str(uuid.uuid4())[:8]
    config_data = request.config
    
    method_map = {
        "±5%": SamplingMethod.PERCENTAGE_5,
        "±10%": SamplingMethod.PERCENTAGE_10,
        "latin_hypercube": SamplingMethod.LATIN_HYPERCUBE,
        "sobol": SamplingMethod.SOBOL,
        "monte_carlo": SamplingMethod.MONTE_CARLO
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
                max_value=p.get("max_value")
            )
            for p in params_list
        ]
        
        perturbable_count = sum(1 for p in params if p.perturbable)
        base_n = config_data.get("num_runs", 15)
        
        # Check plan limits before proceeding
        await check_plan_limits(base_n, method_str, user)
        
        actual_run_count = base_n * (perturbable_count + 2) if method == SamplingMethod.SOBOL else base_n
        
        robustness_config = RobustnessConfig(
            enabled=True,
            num_runs=base_n,
            sampling_method=method,
            parameters=params,
            random_seed=config_data.get("random_seed")
        )
        
        # Token Escrow (cost calculation)
        price = 2 if method == SamplingMethod.SOBOL else 5
        cost = actual_run_count * price + 50
        
        job_state = {
            "run_id": run_id,
            "user_id": user["user_id"],
            "plan": user.get("plan", "free"),
            "status": "running",
            "progress": {"current": 0, "total": actual_run_count},
            "created_at": datetime.now().isoformat(),
            "escrowed": cost,
            "config_summary": {
                "method": method_str, 
                "base_n": base_n, 
                "total": actual_run_count,
                "seed": config_data.get("random_seed")
            }
        }
        set_job(run_id, job_state)
        
        # Store idempotency key
        if x_idempotency_key:
            store_idempotency(x_idempotency_key, user["user_id"], run_id)
        
        background_tasks.add_task(execute_robustness_task, run_id, robustness_config, user)
        
        return JobResponse(
            run_id=run_id,
            status="running",
            progress={"current": 0, "total": actual_run_count},
            created_at=job_state["created_at"]
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
            detail={"message": "PDF export is only available on Professional and Enterprise tiers."}
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
        headers={"Content-Disposition": f"attachment; filename=SimHPC_{run_id}.pdf"}
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
            config, 
            run_id=run_id, 
            progress_callback=update_progress
        )
        
        # Build AI report input with full metadata
        report_input = service.create_ai_report_input_with_metadata(
            summary, 
            simulation_id=run_id
        )
        
        # Generate AI report if allowed by plan
        plan = UserPlan(user.get("plan", UserPlan.FREE))
        ai_report_data = None
        pdf_url = None
        
        if PLAN_LIMITS[plan].get("ai_reports"):
            # Use RunPod Serverless if configured, otherwise fallback to local Kimi/Template
            if RUNPOD_API_KEY and RUNPOD_ENDPOINT_ID:
                try:
                    logger.info(f"Offloading to RunPod Serverless: {run_id}")
                    runpod = RunPodClient(RUNPOD_API_KEY, RUNPOD_ENDPOINT_ID)
                    
                    # Send input to RunPod
                    # The worker's handler.py expects 'prompt'
                    runpod_input = {
                        "prompt": f"Analyze these simulation results: {json.dumps(report_input)}",
                        "simulation_id": run_id,
                        "metadata": report_input
                    }
                    
                    rp_job_id = await runpod.run_job(runpod_input)
                    rp_output = await runpod.wait_for_job(rp_job_id)
                    
                    # rp_output is the return from handler.py: {"status": "complete", "result": "...", "pdf_url": "..."}
                    ai_report_data = {
                        "summary": rp_output.get("result"),
                        "analysis": "Generated by RunPod Mercury Engine",
                        "recommendations": ["Review the attached PDF for full technical details."],
                        "version": "runpod-alpha-1"
                    }
                    pdf_url = rp_output.get("pdf_url")
                    logger.info(f"RunPod processing complete for {run_id}. PDF: {pdf_url}")
                    
                except Exception as rp_error:
                    logger.error(f"RunPod failed, falling back to local AI: {rp_error}")
                    # Fallback to local
                    ai_report = ai_service.generate_report(report_input, user_id=user.get("user_id"))
                    ai_report_data = ai_report.to_dict()
            else:
                # Standard local generation
                ai_report = ai_service.generate_report(report_input, user_id=user.get("user_id"))
                ai_report_data = ai_report.to_dict()
        
        job = get_job(run_id)
        if job:
            # Use atomic field updates instead of full replace
            update_job_field(run_id, "status", "completed")
            update_job_field(run_id, "completed_at", datetime.now().isoformat())
            update_job_field(run_id, "results", {
                "baseline": summary.baseline_result.__dict__,
                "sensitivity": [s.__dict__ for s in summary.sensitivity_ranking],
                "stats": {
                    "variance": summary.variance, 
                    "std_dev": summary.standard_deviation,
                    "confidence_interval": summary.confidence_interval_percent,
                    "non_convergent_count": summary.non_convergent_count
                }
            })
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
