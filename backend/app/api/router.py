from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from backend.app.api.admin.observability import router as observability_router
from backend.app.api.endpoints.simulations import router as simulations_router
from backend.app.api.routes import certificates, onboarding
from backend.app.api.routes.alpha import router as alpha_router

api_router = APIRouter()

api_router.include_router(observability_router, prefix="/admin", tags=["Admin"])
api_router.include_router(simulations_router, prefix="/simulations", tags=["Simulations"])
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["Onboarding"])
api_router.include_router(certificates.router, prefix="/certificates", tags=["Verification"])
api_router.include_router(alpha_router, prefix="/alpha", tags=["Alpha"])

app = FastAPI(title="SimHPC API", version="3.5.0")

# --- v3.5 SECURITY: CORS ---
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "api-online", "version": "3.5.0"}
