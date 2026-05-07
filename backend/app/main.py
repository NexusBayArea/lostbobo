import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.api_router import api_router
from backend.core.gateway.gateway import GovernanceMiddleware
from backend.core.governance.metrics import metrics_app
from backend.core.governance.simulation_worker import start_simulation_worker

app = FastAPI(title="SimHPC Core Orchestrator", version="3.5.0")

app.mount("/metrics", metrics_app)

# --- v3.5 SECURITY: CORS & INFISICAL ---
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware, allow_origins=[FRONTEND_URL], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

app.add_middleware(GovernanceMiddleware)

# --- ROUTER INTEGRATION ---
app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
async def startup():
    await start_simulation_worker()


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "3.5.0", "environment": os.getenv("ENV", "dev")}
