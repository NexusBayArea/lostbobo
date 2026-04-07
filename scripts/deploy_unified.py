#!/usr/bin/env python3
import os
import runpod

API_KEY = os.getenv("RUNPOD_API_KEY")
if not API_KEY:
    raise ValueError("RUNPOD_API_KEY environment variable not set")

runpod.api_key = API_KEY

print("=== Deploying SimHPC Unified Pod ===")

new_pod = runpod.create_pod(
    name="SimHPC-Unified-v2.5.5",
    image_name="simhpcworker/simhpc-unified:latest",
    gpu_type_id="NVIDIA A40",
    gpu_count=1,
    volume_in_gb=20,
    container_disk_in_gb=20,
    ports="8000/http",
    env={"PYTHONUNBUFFERED": "1"},
)

print(f"Pod ID: {new_pod['id']}")
print(f"HTTP Proxy: https://{new_pod['id']}-8000.proxy.runpod.net")
