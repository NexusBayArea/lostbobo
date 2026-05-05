from fastapi import APIRouter

from backend.app.api.admin.observability import router as observability_router
from backend.app.api.dag import router as dag_router
from backend.app.api.endpoints.simulations import router as simulations_router
from backend.app.api.reports import router as reports_router
from backend.app.api.routes import certificates, onboarding
from backend.app.api.routes.alpha import router as alpha_router

api_router = APIRouter()

api_router.include_router(dag_router, prefix="", tags=["DAG"])
api_router.include_router(observability_router, prefix="/admin", tags=["Admin"])
api_router.include_router(simulations_router, prefix="/simulations", tags=["Simulations"])
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["Onboarding"])
api_router.include_router(certificates.router, prefix="/certificates", tags=["Verification"])
api_router.include_router(alpha_router, prefix="/alpha", tags=["Alpha"])
api_router.include_router(reports_router, prefix="/reports", tags=["Reports"])
