import os
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.admin.observability import router as observability_router
from backend.app.api.endpoints.simulations import router as simulations_router
from backend.app.api.routes import certificates, onboarding
from backend.app.api.routes.alpha import router as alpha_router

app = FastAPI(title="SimHPC Gateway", version="3.5.0")

# Centralized CORS Policy
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gateway Routes
app.include_router(observability_router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(simulations_router, prefix="/api/v1/simulations", tags=["Simulations"])
app.include_router(onboarding.router, prefix="/api/v1/onboarding", tags=["Onboarding"])
app.include_router(certificates.router, prefix="/api/v1/certificates", tags=["Verification"])
app.include_router(alpha_router, prefix="/api/v1/alpha", tags=["Alpha"])


@app.get("/health")
async def health_check():
    return {"status": "gateway-online", "timestamp": datetime.now().isoformat()}
