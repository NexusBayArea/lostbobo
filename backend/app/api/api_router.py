from fastapi import APIRouter

from app.api.admin.observability import router as observability_router
from app.api.endpoints.simulations import router as simulations_router
from app.api.routes import certificates, onboarding
from app.api.routes.alpha import router as alpha_router

api_router = APIRouter()

api_router.include_router(observability_router, prefix="/admin", tags=["Admin"])
api_router.include_router(simulations_router, prefix="/simulations", tags=["Simulations"])
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["Onboarding"])
api_router.include_router(certificates.router, prefix="/certificates", tags=["Verification"])
api_router.include_router(alpha_router, prefix="/alpha", tags=["Alpha"])
