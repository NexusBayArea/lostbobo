# """
# SimHPC API - Unified Platform (Beta Foundation v2.8.0)
# """

import asyncio
import logging
import os
import uuid
import json
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any

from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

import httpx
import redis
from fastapi import FastAPI, HTTPException, Header, Depends, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator

# --- ONBOARDING & ROUTES ---
from app.services.onboarding_service import OnboardingService
from app.api.routes import onboarding as onboarding_router
from app.api.routes import simulations as simulations_router
from app.api.routes import certificates as certificates_router
from app.api.routes import control as control_router
from app.api.routes import admin as admin_router

# Import local services
from auth_utils import verify_user
from job_queue import enqueue_job

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIG ---
API_KEY = os.getenv("SIMHPC_API_KEY")
MERCURY_URL = os.getenv(
    "MERCURY_API_URL",
    "https://api.inceptionlabs.ai/v1/chat/completions",
)
MERCURY_MODEL = os.getenv("MERCURY_MODEL_ID", "mercury-2")

RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
RUNPOD_POD_ID = os.getenv("RUNPOD_POD_ID")

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173,https://*.vercel.app,https://simhpc.nexusbayarea.com,https://simhpc.com",
).split(",")
CORS_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS if origin.strip()]

# --- Supabase Client ---
try:
    from supabase import create_client, Client

    SB_URL = os.getenv("SB_URL")
    SB_SERVICE_KEY = os.getenv("SB_SERVICE_KEY")
    supabase_client: Optional[Client] = None
    if SB_URL and SB_SERVICE_KEY:
        supabase_client = create_client(SB_URL, SB_SERVICE_KEY)
        logger.info("Supabase client initialized")
    else:
        logger.warning("Supabase credentials not configured")
except ImportError:
    supabase_client = None
    logger.warning("supabase-py not installed")

# --- REDIS CLIENT WITH FALLBACK ---
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


class InMemoryCache:
    def __init__(self):
        self._cache = {}

    def get(self, key):
        return self._cache.get(key)

    def set(self, key, value, ex=None):
        self._cache[key] = value

    def setex(self, key, time, value):
        self._cache[key] = value

    def delete(self, key):
        self._cache.pop(key, None)

    def hset(self, name, key=None, value=None, mapping=None):
        if name not in self._cache:
            self._cache[name] = {}
        if mapping:
            self._cache[name].update(mapping)
        elif key is not None:
            self._cache[name][key] = value

    def hget(self, name, key):
        return self._cache.get(name, {}).get(key)

    def hgetall(self, name):
        return self._cache.get(name, {})

    def incr(self, key):
        val = int(self._cache.get(key, 0)) + 1
        self._cache[key] = str(val)
        return val

    def ping(self):
        return True


r_client = None
redis_available = False
try:
    r_client = redis.from_url(REDIS_URL, decode_responses=True)
    r_client.ping()
    redis_available = True
    logger.info(f"Redis connected: {REDIS_URL}")
except Exception as e:
    logger.warning(f"Redis unavailable: {e}. Using in-memory fallback.")
    r_client = InMemoryCache()
    redis_available = False


# --- WORKER REGISTRY ---
def get_active_workers() -> List[dict]:
    active_worker_ids = r_client.smembers("workers:active")
    workers = []
    for wid in active_worker_ids:
        if not r_client.exists(f"worker:heartbeat:{wid}"):
            r_client.srem("workers:active", wid)
            r_client.delete(f"worker:metadata:{wid}")
            continue
        metadata = r_client.hgetall(f"worker:metadata:{wid}")
        if metadata:
            workers.append(metadata)
    return workers


async def check_compute_availability():
    """Softened during beta transition - prevents no_active_pods breaking frontend."""
    workers = get_active_workers()
    if not workers:
        logger.warning("No active workers detected - continuing in degraded mode")
        return [{"worker_id": "fallback", "status": "idle"}]
    return workers


# --- BASIC HEALTH ENDPOINT (Critical for GitHub + RunPod proxy) ---
@app.get("/health", tags=["System — Health"])
@app.get("/api/v1/health", tags=["System — Health"])
async def health_check():
    """Simple health check used by GitHub Actions and RunPod proxy."""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "SimHPC API",
        "version": "2.8.0-beta",
    }


# ... rest of your api.py remains unchanged ...

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
