from locust import HttpUser, task, between

class SimHPCUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def simulate_task(self):
        self.client.post("/api/v1/orchestrator/run", json={"query": "Test query", "tenant_id": "public"})

    @task
    def health_check(self):
        self.client.get("/health")
