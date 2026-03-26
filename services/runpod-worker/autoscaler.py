import os
import time
import requests
import redis
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# RunPod API Configuration
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Scaling Policy
MAX_PODS = int(os.getenv("MAX_PODS", 2))
MIN_PODS = int(os.getenv("MIN_PODS", 0))
IDLE_TIMEOUT = int(os.getenv("IDLE_TIMEOUT_SEC", 300))
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_SEC", 10))

# Queue/Metrics
QUEUE_NAME = os.getenv("QUEUE_NAME", "simhpc_jobs")
INFLIGHT_KEY = os.getenv("INFLIGHT_KEY", "simhpc_inflight")

# GPU Policy
DEFAULT_GPU = os.getenv("DEFAULT_GPU", "NVIDIA A40")
FALLBACK_GPU = os.getenv("FALLBACK_GPU", "NVIDIA RTX 3090")
MAX_JOBS_PER_GPU = int(os.getenv("MAX_JOBS_PER_GPU", 2))

# Container Config
RUNPOD_IMAGE = os.getenv("RUNPOD_IMAGE", "simhpcworker/simhpc-worker:v2.2.0")

HEADERS = {
    "Authorization": f"Bearer {RUNPOD_API_KEY}",
    "Content-Type": "application/json"
}

r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# ---------------------------
# RunPod API Helpers
# ---------------------------

def list_pods():
    try:
        res = requests.get("https://api.runpod.io/v1/pods", headers=HEADERS)
        if res.status_code == 200:
            return res.json().get("pods", [])
        print(f"Error listing pods: {res.text}")
        return []
    except Exception as e:
        print(f"API Error: {e}")
        return []

def stop_pod(pod_id):
    print(f"Stopping idle pod: {pod_id}")
    requests.post(f"https://api.runpod.io/v1/pods/{pod_id}/stop", headers=HEADERS)

def create_pod(gpu_type):
    print(f"Creating new pod with {gpu_type}...")
    payload = {
        "name": f"simhpc-worker-{int(time.time())}",
        "imageName": RUNPOD_IMAGE,
        "gpuTypeId": gpu_type,
        "cloudType": "SECURE",
        "containerDiskInGb": 20,
        "env": [
            {"key": "REDIS_URL", "value": REDIS_URL},
            {"key": "QUEUE_NAME", "value": QUEUE_NAME},
            {"key": "INFLIGHT_KEY", "value": INFLIGHT_KEY},
        ]
    }
    res = requests.post("https://api.runpod.io/v1/pods", headers=HEADERS, json=payload)
    pod = res.json()
    return pod.get("id")

# ---------------------------
# Metrics
# ---------------------------

def queue_length():
    return r.llen(QUEUE_NAME)

def inflight_jobs():
    val = r.get(INFLIGHT_KEY)
    return int(val) if val else 0

def active_pods():
    pods = list_pods()
    # desiredStatus RUNNING means it should be up or coming up
    return [p for p in pods if p.get("desiredStatus") == "RUNNING"]

# ---------------------------
# Scaling Logic
# ---------------------------

def desired_pods(q_len, inflight):
    total_jobs = q_len + inflight
    if total_jobs == 0:
        return MIN_PODS
    needed = (total_jobs + MAX_JOBS_PER_GPU - 1) // MAX_JOBS_PER_GPU
    return max(MIN_PODS, min(MAX_PODS, needed))

def scale_up(current, target):
    to_add = target - current
    for _ in range(to_add):
        pod_id = create_pod(DEFAULT_GPU)
        if pod_id:
            r.sadd("pods:active", pod_id)
            r.set(f"pods:last_used:{pod_id}", int(time.time()))

def scale_down(pods):
    now = int(time.time())
    for p in pods:
        pod_id = p["id"]
        last_used = r.get(f"pods:last_used:{pod_id}")
        last_used = int(last_used) if last_used else now
        
        if now - last_used > IDLE_TIMEOUT:
            stop_pod(pod_id)
            r.srem("pods:active", pod_id)

# ---------------------------
# Main Loop
# ---------------------------

def run():
    print(f"SimHPC Production Autoscaler Started (v2.2.1)")
    print(f"Policy: MIN={MIN_PODS}, MAX={MAX_PODS}, IDLE={IDLE_TIMEOUT}s")
    
    while True:
        try:
            q_len = queue_length()
            inflight = inflight_jobs()
            pods = active_pods()

            current = len(pods)
            target = desired_pods(q_len, inflight)

            print(f"[{datetime.now().strftime('%H:%M:%S')}] Q={q_len} INF={inflight} Pods={current} Target={target}")

            if target > current:
                scale_up(current, target)
            elif q_len == 0 and inflight == 0:
                # Only scale down if everything is idle
                scale_down(pods)

        except Exception as e:
            print(f"Autoscaler Error: {e}")

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    run()
