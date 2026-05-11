import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.admin.cost_admin import router as cost_admin_router
from backend.app.api.api_router import api_router
from backend.core.gateway.gateway import SecurityGatewayMiddleware
from backend.core.governance.health import validate_governance_secrets
from backend.core.governance.metrics import metrics_app
from backend.core.governance.simulation_worker import start_simulation_worker
from backend.core.middleware.enforcement import register_middleware
from backend.core.security.infisical import infisical_jit_inject

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    log.info("Starting SimHPC with Security/Governance Gateway...")
    infisical_jit_inject()
    await validate_governance_secrets()
    await start_simulation_worker()

    from backend.core.services.observability_service import observability
    from backend.core.services.tracing import setup_tracing

    setup_tracing("simhpc")
    observability()
    log.info("Observability + OpenTelemetry initialized")

    from backend.ml.training.exporter import TrainingDataExporter

    exporter = TrainingDataExporter()
    stats = await exporter.get_dataset_stats()
    if stats.get("ready_for_training"):
        log.info("ML training data ready — consider running export")
    else:
        log.info(f"ML accumulating data: {stats.get('total_qualified_runs', 0)} qualified runs")

    yield
    # Shutdown
    log.info("Shutting down...")


app = FastAPI(title="SimHPC Core Orchestrator", version="3.5.0", lifespan=lifespan)

app.mount("/metrics", metrics_app)

# --- v3.5 SECURITY: CORS & INFISICAL ---
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware, allow_origins=[FRONTEND_URL], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

app.add_middleware(SecurityGatewayMiddleware)

# --- ROUTER INTEGRATION ---
app.include_router(api_router, prefix="/api/v1")
app.include_router(cost_admin_router, prefix="/api/v1")

# --- MIDDLEWARE INTEGRATION ---
register_middleware(app)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "3.5.0", "environment": os.getenv("ENV", "dev")}
