import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.admin.observability import router as observability_router
from backend.app.api.endpoints.simulations import router as simulations_router
from backend.app.api.routes.alpha import router as alpha_router
from backend.app.api.routes import onboarding, certificates

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
# Observability for your AdminAnalyticsPage.tsx
app.include_router(observability_router, prefix="/api/v1/admin", tags=["Admin"])

# Simulation Logic (The Core)
app.include_router(simulations_router, prefix="/api/v1/simulations", tags=["Simulations"])

# Onboarding & Credits (The Economy)
app.include_router(onboarding.router, prefix="/api/v1/onboarding", tags=["Onboarding"])

# The Moat: Verification & PDFs
app.include_router(certificates.router, prefix="/api/v1/certificates", tags=["Verification"])

# Legacy Alpha shim (Temporary)
app.include_router(alpha_router, prefix="/api/v1/alpha", tags=["Alpha"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "3.5.0", "environment": os.getenv("ENV", "dev")}
