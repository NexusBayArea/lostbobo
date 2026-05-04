import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.api_router import api_router

app = FastAPI(title="SimHPC Core Orchestrator", version="3.5.0")

# --- v3.5 SECURITY: CORS & INFISICAL ---
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROUTER INTEGRATION ---
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "3.5.0", "environment": os.getenv("ENV", "dev")}
