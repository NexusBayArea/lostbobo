import structlog
from prometheus_client import Counter, Gauge, Histogram, Info

from backend.core.kernel.kernel import Kernel
from backend.core.supabase_job_store import SupabaseJobStore

log = structlog.get_logger(__name__)


class MonitoringService:
    """Kernel-centered Prometheus metrics service."""

    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.supabase = SupabaseJobStore()

        # === Core Counters ===
        self.requests_total = Counter(
            "simhpc_requests_total", "Total HTTP requests", ["method", "route", "tenant_id", "status"]
        )
        self.request_duration = Histogram("simhpc_request_duration_seconds", "Request latency", ["route", "tenant_id"])
        self.trust_verifications = Counter(
            "simhpc_trust_verifications_total", "Trust Runtime verifications", ["decision", "tenant_id"]
        )
        self.genai_fallbacks = Counter(
            "simhpc_genai_fallbacks_total", "GenAI fallback events", ["component", "tenant_id"]
        )
        self.chaos_experiments = Counter("simhpc_chaos_experiments_total", "Chaos experiments run", ["experiment_type"])
        self.swarm_tasks = Counter("simhpc_swarm_tasks_total", "Swarm agent tasks", ["agent_type", "status"])

        # Gauges
        self.active_users = Gauge("simhpc_active_users", "Current active tenants/users")
        self.world_model_state_size = Gauge("simhpc_world_model_state_size", "World Model entities tracked")
        self.physics_simulation_queue = Gauge("simhpc_physics_queue_depth", "Pending physics jobs")

        # Info
        self.build_info = Info("simhpc_build_info", "Build information")
        self.build_info.info({"version": "0.4.0", "commit": "latest"})

    async def record_request(self, method: str, route: str, status: int, duration: float, tenant_id: str = "unknown"):
        self.requests_total.labels(method=method, route=route, tenant_id=tenant_id, status=str(status)).inc()
        self.request_duration.labels(route=route, tenant_id=tenant_id).observe(duration)

        # Persist key metrics to Supabase for long-term truth
        if status >= 400 or duration > 5.0:
            await self.supabase.record_event(
                "high_latency_or_error",
                {"route": route, "status": status, "duration": duration, "tenant_id": tenant_id},
            )

    async def record_trust_verification(self, decision: str, score: float, tenant_id: str):
        self.trust_verifications.labels(decision=decision, tenant_id=tenant_id).inc()
        await self.supabase.save_metrics("trust", {"decision": decision, "score": score, "tenant_id": tenant_id})

    async def record_genai_fallback(self, component: str, tenant_id: str):
        self.genai_fallbacks.labels(component=component, tenant_id=tenant_id).inc()
