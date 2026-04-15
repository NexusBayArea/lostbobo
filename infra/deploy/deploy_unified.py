#!/usr/bin/env python3
import os
import sys
import runpod

# 1. Capture the API Key from Infisical (via os.getenv)
API_KEY = os.getenv("RUNPOD_API_KEY")
# Capture the token that will authenticate the cloud container
INFISICAL_TOKEN = os.getenv("INFISICAL_TOKEN")

if not API_KEY:
    print("❌ ERROR: RUNPOD_API_KEY not found. Run with 'infisical run -- python3 ...'")
    sys.exit(1)

if not INFISICAL_TOKEN:
    print(
        "⚠️  WARNING: INFISICAL_TOKEN is missing. The pod will boot but fail to pull secrets."
    )

runpod.api_key = API_KEY

print("=== Deploying SimHPC Unified Pod (v2.5.11) ===")

try:
    # 2. Create the Pod
    new_pod = runpod.create_pod(
        name="SimHPC-Unified-v2.5.11",
        image_name="simhpcworker/simhpc-unified:latest",
        gpu_type_id="NVIDIA A40",
        gpu_count=1,
        volume_in_gb=20,
        container_disk_in_gb=20,
        ports="8080/http,8000/http",
        env={"PYTHONUNBUFFERED": "1", "INFISICAL_TOKEN": INFISICAL_TOKEN},
    )

    # 3. Print the Pod ID clearly for the CLI to capture
    # Note: runpod-python returns a dictionary; the ID is in ['id']
    pod_id = new_pod["id"]
    print("\n🚀 DEPLOYMENT SUCCESSFUL")
    print(f"POD_ID: {pod_id}")
    print(f"HTTP_PROXY: https://{pod_id}-8080.proxy.runpod.net")

except Exception as e:
    print(f"❌ DEPLOYMENT FAILED: {e}")
    sys.exit(1)
