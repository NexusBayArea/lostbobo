from locust import HttpUser, task, between
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

# Custom SimHPC Metrics
swarm_requests = Counter("locust_swarm_requests_total", "Total swarm evaluations")
swarm_fallbacks = Counter(
    "locust_swarm_fallbacks_total", "Swarm requests using fallback"
)
rag_latency = Histogram("locust_rag_query_latency_seconds", "RAG query latency")
physics_success = Counter(
    "locust_physics_success_total", "Successful physics simulations"
)
genai_degraded_ratio = Gauge(
    "locust_genai_degraded_ratio", "Current GenAI fallback ratio"
)


class SimHPCUser(HttpUser):
    wait_time = between(0.5, 2.0)

    def on_start(self):
        self.client.headers.update({"X-Tenant-ID": "test-tenant"})
        try:
            start_http_server(8081)
        except Exception:
            pass  # Already running

    @task(3)
    def swarm_forecast(self):
        start_time = time.time()
        payload = {"query": "Test query"}

        with self.client.post(
            "/api/v1/orchestrator/run", json=payload, catch_response=True
        ) as resp:
            time.time() - start_time
            swarm_requests.inc()

            if resp.status_code == 200:
                data = resp.json()
                if data.get("degraded") or "fallback" in str(data):
                    swarm_fallbacks.inc()
                    # Calculate ratio
                    swarm_reqs = swarm_requests._value.get()
                    swarm_falls = swarm_fallbacks._value.get()
                    genai_degraded_ratio.set(swarm_falls / max(swarm_reqs, 1))
                resp.success()
            else:
                resp.failure(f"Failed with {resp.status_code}")

    @task(2)
    def rag_query(self):
        start = time.time()
        with self.client.get("/api/v1/rag/query?q=test"):
            rag_latency.observe(time.time() - start)

    @task(1)
    def physics_simulation(self):
        with self.client.post(
            "/api/v1/physics/simulate", json={"iterations": 100}
        ) as resp:
            if resp.status_code == 200 and resp.json().get("validation_passed"):
                physics_success.inc()
