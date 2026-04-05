"""
RunPod Pod Restart Script

Usage:
    python scripts/restart_runpod_pod.py

Requires:
    - pip install runpod
    - RUNPOD_API_KEY environment variable
    - RUNPOD_POD_ID environment variable (optional - will auto-detect if not set)

This script restarts the RunPod worker pod to pull the latest Docker images.
"""

import os
import sys
import runpod


def get_api_key():
    """Get API key from environment."""
    return os.getenv("RUNPOD_API_KEY")


def get_pod_id():
    """Get pod ID from environment."""
    return os.getenv("RUNPOD_POD_ID")


def restart_pod(api_key: str, pod_id: str):
    """Restart a RunPod pod by stopping and resuming it."""
    runpod.api_key = api_key

    print(f"Stopping pod {pod_id}...")
    stop_result = runpod.stop_pod(pod_id)
    print(f"Stop result: {stop_result}")

    print(f"Resuming pod {pod_id}...")
    resume_result = runpod.resume_pod(pod_id, gpu_count=1)
    print(f"Resume result: {resume_result}")

    return resume_result


def main():
    api_key = get_api_key()
    pod_id = get_pod_id()

    if not api_key:
        print("Error: RUNPOD_API_KEY not found. Set env var.")
        sys.exit(1)

    if not pod_id:
        print("RUNPOD_POD_ID not found, listing available pods...")
        pods = runpod.get_pods()
        if not pods:
            print("No pods found!")
            sys.exit(1)
        pod_id = pods[0]["id"]
        print(f"Using pod: {pod_id}")

    restart_pod(api_key, pod_id)
    print("Pod restarted successfully!")


if __name__ == "__main__":
    main()
