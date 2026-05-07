from prometheus_client import Counter, Gauge, Histogram, make_asgi_app

# Governance Metrics
governance_requests = Counter(
    "governance_requests_total", "Total governance checks", ["status", "operation", "tenant_id"]
)

governance_blocked = Counter("governance_blocked_total", "Requests blocked by governance", ["reason", "operation"])

token_usage = Counter("governance_token_usage_total", "Tokens consumed under governance", ["tenant_id", "operation"])

simulation_queue_depth = Gauge("simulation_queue_depth", "Current simulation queue depth by priority", ["priority"])

active_streams = Gauge("active_streams", "Currently active RAG streams")

governance_latency = Histogram(
    "governance_check_latency_seconds",
    "Latency of governance checks",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25],
)


def record_governance_metric(name: str, labels: dict[str, str] = None):
    """Called from ComputeGovernance"""
    if name == "governance_allowed":
        governance_requests.labels(status="allowed", **(labels or {})).inc()
    elif name == "governance_blocked":
        governance_blocked.labels(**labels).inc()
    elif name == "token_usage":
        token_usage.labels(**labels).inc()


# Expose metrics endpoint
metrics_app = make_asgi_app()
