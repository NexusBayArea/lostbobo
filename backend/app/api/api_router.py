from fastapi import APIRouter

from backend.api.routes.governance import router as governance_router
from backend.app.api.admin.observability import router as observability_router
from backend.app.api.agent_routes import router as agent_router
from backend.app.api.auth import router as auth_router
from backend.app.api.capability_invoke import router as capability_router
from backend.app.api.dag import router as dag_router
from backend.app.api.endpoints.simulations import router as simulations_router
from backend.app.api.graph_viz import router as graph_viz_router
from backend.app.api.graphrag import router as graphrag_router
from backend.app.api.hardware import router as hardware_router
from backend.app.api.ml import router as ml_router
from backend.app.api.reports import router as reports_router
from backend.app.api.routes import certificates, onboarding
from backend.app.api.routes.alpha import router as alpha_router
from backend.app.api.routes.auto_research import router as auto_research_router
from backend.app.api.routes.discovery import router as discovery_router
from backend.app.api.routes.memory import router as memory_router
from backend.app.api.routes.observational import router as observational_router
from backend.app.api.routes.skills import router as skill_router
from backend.app.api.sla_monitor import router as sla_monitor_router
from backend.app.api.webhooks.alerts import router as webhook_router
from backend.app.api.world_routes import router as world_router
from backend.app.api.world_state import router as world_state_router
from backend.core.services.beam_orchestrator_service import router as orchestrator_router
from backend.runtime.grid.api import router as grid_router
from backend.runtime.swarm.api import router as swarm_api_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/api", tags=["Auth"])
api_router.include_router(dag_router, prefix="", tags=["DAG"])
api_router.include_router(observability_router, prefix="/admin", tags=["Admin"])
api_router.include_router(simulations_router, prefix="/simulations", tags=["Simulations"])
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["Onboarding"])
api_router.include_router(certificates.router, prefix="/certificates", tags=["Verification"])
api_router.include_router(alpha_router, prefix="/alpha", tags=["Alpha"])
api_router.include_router(reports_router, prefix="/reports", tags=["Reports"])
api_router.include_router(graphrag_router, prefix="/graphrag", tags=["GraphRAG"])
api_router.include_router(sla_monitor_router, prefix="/sla", tags=["SLAMonitoring"])
api_router.include_router(memory_router, prefix="/memory", tags=["Memory"])
api_router.include_router(agent_router, prefix="/agents", tags=["Agents"])
api_router.include_router(world_router, prefix="/world_model", tags=["WorldModel"])
api_router.include_router(skill_router, prefix="/skills", tags=["Skills"])
api_router.include_router(orchestrator_router, prefix="/orchestrator", tags=["Orchestrator"])
api_router.include_router(auto_research_router, prefix="/auto-research", tags=["AutoResearch"])
api_router.include_router(observational_router, prefix="/observational", tags=["Observational"])
api_router.include_router(governance_router, prefix="/governance", tags=["Governance"])
api_router.include_router(swarm_api_router, prefix="", tags=["SwarmAPI"])
api_router.include_router(grid_router, prefix="", tags=["ExperimentGrid"])
api_router.include_router(discovery_router, prefix="/api/v1", tags=["DiscoveryGraph"])
api_router.include_router(ml_router, prefix="/api/v1/ml", tags=["ML"])
api_router.include_router(webhook_router, prefix="/api/v1", tags=["AlertWebhooks"])
api_router.include_router(world_state_router, prefix="/api/v1", tags=["WorldState"])
api_router.include_router(graph_viz_router, prefix="/api/v1", tags=["Visualization"])
api_router.include_router(capability_router, tags=["Capability"])
api_router.include_router(hardware_router, prefix="/api/v1", tags=["Hardware"])
api_router.include_router(sla_monitor_router, prefix="/sla", tags=["SLAMonitoring"])
