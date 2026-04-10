#!/usr/bin/env python3
import sys
import subprocess

# Configuration - Centralized for easy updates
IMAGE_NAME = "simhpcworker/simhpc-worker:latest"
POD_NAME = "SimHPC_P_01"
GPU_TYPE = "NVIDIA A40"


def run_command(cmd, check=True):
    print(f"🚀 Running: {cmd}")
    # Using list for subprocess is safer than shell=True where possible
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0 and check:
        print(f"❌ Error: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()


def get_secret(name):
    """Refined Infisical fetcher with fallback handling."""
    try:
        # Use --plain and handle potential Windows 'cmd /c' wrapping
        cmd = f"infisical secrets get {name} --plain"
        val = run_command(cmd)
        return val.split("\n")[-1]  # Ensure we get the last line (the value)
    except Exception:
        print(f"⚠️ Warning: Secret {name} not found. Using None.")
        return None


def deploy():
    print("=== 🛠️ SimHPC Optimized Deployment ===\n")

    # 1. Gather Essentials
    api_key = get_secret("RUNPOD_API_KEY")
    old_pod_id = get_secret("RUNPOD_ID")

    env_vars = {
        "REDIS_URL": get_secret("REDIS_URL"),
        "MERCURY_API_KEY": get_secret("MERCURY_API_KEY"),
        "PYTHONUNBUFFERED": "1",  # Good practice for Docker logs
    }

    # 2. Build and Push (Optimized)
    print("=== 📦 Building & Pushing Image ===")
    # Using buildx ensures the image layer is clean
    run_command(f"docker build -f Dockerfile.worker -t {IMAGE_NAME} .")
    run_command(f"docker push {IMAGE_NAME}")

    # 3. RunPod Orchestration
    import runpod

    runpod.api_key = api_key

    # Check if we should terminate or just update (Safe approach)
    if old_pod_id:
        print(f"🛑 Terminating old pod: {old_pod_id}")
        try:
            runpod.terminate_pod(old_pod_id)
        except Exception as e:
            print(f"Pod termination skipped: {e}")

    print(f"✨ Creating new GPU Pod: {GPU_TYPE}")
    new_pod = runpod.create_pod(
        name=POD_NAME,
        image_name=IMAGE_NAME,
        gpu_type_id=GPU_TYPE,
        gpu_count=1,
        volume_in_gb=20,
        container_disk_in_gb=20,
        ports="8080/http,8000/http,22/tcp",
        env=env_vars,
    )

    new_id = new_pod["id"]

    # 4. Sync Secrets
    print(f"🔒 Syncing new Pod ID to Infisical: {new_id}")
    run_command(f"infisical secrets set RUNPOD_ID={new_id}")

    print("\n✅ Deployment Successful!")
    print(f"🔗 API URL: https://{new_id}-8080.proxy.runpod.net")


if __name__ == "__main__":
    deploy()
