import time
import requests


class SimHPCClient:
    """
    Python SDK for SimHPC Platform.
    Enables automation of robustness sweeps, telemetry monitoring, and batch optimization.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://8qvtqsc4zl5tms-8000.proxy.runpod.net/api/v1",
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json", "X-API-Key": api_key}

    def start_robustness_sweep(self, config: dict):
        """Trigger a Robustness Sweep (Sensitivity Analysis)"""
        print(
            f"🚀 Triggering Robustness Sweep ({config.get('num_runs', 15)} samples)..."
        )
        response = requests.post(
            f"{self.base_url}/robustness/run",
            headers=self.headers,
            json={"config": config},
        )
        response.raise_for_status()
        return response.json()["run_id"]

    def get_status(self, run_id: str):
        """Poll for completion using internal status polling logic"""
        response = requests.get(
            f"{self.base_url}/robustness/status/{run_id}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def cancel_run(self, run_id: str):
        """Cancel and Refund Credits"""
        response = requests.post(
            f"{self.base_url}/robustness/cancel/{run_id}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def download_report(self, run_id: str, output_path: str):
        """Export the defensible PDF report"""
        response = requests.get(
            f"{self.base_url}/robustness/report/{run_id}/pdf",
            headers=self.headers,
            stream=True,
        )
        response.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"✅ Report downloaded to {output_path}")


# Example Usage: Batch Optimization Loop
if __name__ == "__main__":
    client = SimHPCClient(api_key="shpc_live_8qvtqsc4zl5tms")

    # Target: Find thermal conductivity that minimizes peak temperature
    # while maintaining stability within a ±10% robustness window.

    conductivity_candidates = [0.8, 1.2, 1.6]
    best_candidate = None
    min_variance = float("inf")

    print("🛠️ Starting Batch Optimization Loop...")

    for k in conductivity_candidates:
        print(f"\n--- Testing Conductivity: {k} W/(m·K) ---")

        config = {
            "num_runs": 10,
            "sampling_method": "±10%",
            "parameters": [
                {"name": "thermal_conductivity", "base_value": k, "perturbable": True},
                {"name": "boundary_flux", "base_value": 1200.0, "perturbable": True},
            ],
            "random_seed": 42,  # Enforce reproducibility for comparison
        }

        run_id = client.start_robustness_sweep(config)

        # Simple polling loop
        while True:
            status = client.get_status(run_id)
            if status["status"] in ["completed", "failed"]:
                break
            print(
                f"⏳ Progress: {status['progress']['current']}/{status['progress']['total']}"
            )
            time.sleep(5)

        if status["status"] == "completed":
            results = status["results"]
            variance = results["stats"]["variance"]
            max_temp = results["baseline"]["max_temperature"]

            print(
                f"✅ Run {run_id} Complete. Max Temp: {max_temp:.1f}K, Variance: {variance:.2f}"
            )

            if variance < min_variance:
                min_variance = variance
                best_candidate = k
        else:
            print(f"❌ Run {run_id} failed.")

    print(
        f"\n🏆 Optimization Complete. Best Conductivity: {best_candidate} (Variance: {min_variance:.2f})"
    )
