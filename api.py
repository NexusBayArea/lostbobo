"""
SimHPC API - Unified Platform (Beta Foundation v2.8.0)
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from app.api.routes import admin as admin_router
from app.api.routes import certificates as certificates_router
from app.api.routes import control as control_router
from app.api.routes import onboarding as onboarding_router
from app.api.routes import simulations as simulations_router

# 1. Initialize Environment & App immediately to prevent E402/F821
# Note: For Infisical compatibility, we don't load .env here in production
# Infisical injects env vars directly: `infisical run -- python app/main.py`
# We keep this for local development fallback
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

app = FastAPI(title="SimHPC API", version="2.6.7")

# 2. Optimized CORS (Credentials=True requires explicit origins, no wildcards)
allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin for origin in allowed_origins if origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    admin_router.router, prefix="/api/v1/admin", tags=["Admin — Fleet Management"]
)
app.include_router(
    simulations_router.router, prefix="/api/v1/simulations", tags=["Simulations — Core"]
)
app.include_router(
    onboarding_router.router,
    prefix="/api/v1/onboarding",
    tags=["Onboarding — User Management"],
)
app.include_router(
    certificates_router.router,
    prefix="/api/v1/certificates",
    tags=["Certificates — Security"],
)
app.include_router(
    control_router.router,
    prefix="/api/v1/control",
    tags=["Control — System Operations"],
)


# --- MOCK REDIS FOR LOCAL/INFISICAL OVERRIDE ---
class MockRedis:
    def __init__(self):
        self._cache = {}

    def get(self, key):
        return self._cache.get(key)

    def set(self, key, value):
        self._cache[key] = value

    def setex(self, key, ttl_seconds, value):  # Renamed 'time' to 'ttl_seconds'
        self._cache[key] = value


r_client = MockRedis()


# --- BASIC HEALTH ENDPOINTS ---
@app.get("/health", tags=["System — Health"])
@app.get("/api/v1/health", tags=["System — Health"])
async def health_check():
    """Health check for GitHub Actions and RunPod Proxy."""
    return {"status": "healthy", "version": "2.6.7", "port": 8080}


# --- ADMIN: RUNPOD FLEET MANAGEMENT ---
ADMIN_SECRET = os.getenv("ADMIN_SECRET")


async def verify_admin(x_admin_secret: str = Header(None)):
    if not ADMIN_SECRET:
        raise HTTPException(500, "ADMIN_SECRET not configured")
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(403, "Invalid admin credentials")
    return True


# --- ALPHA SERVICES ---
@app.get("/api/v1/alpha/signals", tags=["Alpha — Signals"])
async def get_alpha_signals():
    return {"signals": ["thermal_drift", "pressure_spike", "mesh_instability"]}


@app.post("/api/v1/alpha/run-simulation", tags=["Alpha — Simulations"])
async def run_alpha_simulation():
    import uuid  # Local import to keep global namespace clean

    return {"status": "ok", "run_id": str(uuid.uuid4())}


if __name__ == "__main__":
    import uvicorn

    # Standardized to Port 8080 per SYSTEM.md
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
