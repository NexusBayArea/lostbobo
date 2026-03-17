import os
import time
import requests
from redis import Redis
from datetime import datetime, timedelta

RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
POD_LABEL_KEY = "simhpc-role"
POD_LABEL_VALUE = "worker"
QUEUE_NAME = "gpu_simulations"
MIN_WORKERS = 1
IDLE_TIMEOUT_MIN = 10
CHECK_INTERVAL_SEC = 30
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

redis_client = Redis.from_url(REDIS_URL, decode_responses=True)


def get_queue_length():
    return redis_client.llen(QUEUE_NAME)


def get_worker_pods():
    headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}"}
    resp = requests.get("https://api.runpod.io/v2/pods", headers=headers, timeout=10)
    if resp.status_code != 200:
        print("RunPod API error:", resp.text)
        return []

    pods = resp.json()
    workers = [
        p
        for p in pods
        if p.get("labels", {}).get(POD_LABEL_KEY) == POD_LABEL_VALUE
        and p["status"] in ["RUNNING", "ACTIVE"]
    ]
    return workers


def stop_pod(pod_id):
    headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}"}
    resp = requests.delete(
        f"https://api.runpod.io/v2/pods/{pod_id}", headers=headers, timeout=10
    )
    if resp.status_code == 200:
        print(f"Stopped idle pod {pod_id}")
    else:
        print(f"Failed to stop pod {pod_id}: {resp.text}")


def main():
    last_active = datetime.utcnow()

    while True:
        queue_len = get_queue_length()
        workers = get_worker_pods()
        worker_count = len(workers)

        now = datetime.utcnow()
        print(f"[{now}] Queue: {queue_len} | Workers: {worker_count}")

        if queue_len > 0:
            last_active = now
        else:
            idle_duration = now - last_active
            if (
                idle_duration > timedelta(minutes=IDLE_TIMEOUT_MIN)
                and worker_count > MIN_WORKERS
            ):
                print(
                    f"Idle for {idle_duration.total_seconds() / 60:.1f} min -> scaling down"
                )
                if workers:
                    oldest = min(workers, key=lambda p: p["startedAt"])
                    stop_pod(oldest["id"])
                last_active = now

        time.sleep(CHECK_INTERVAL_SEC)


if __name__ == "__main__":
    main()
