#!/usr/bin/env python3
"""
SimHPC Deployment - RunPod Unified
"""

import subprocess
import sys
import time

import requests

IMAGE_NAME = "simhpcworker/simhpc-unified:latest"
POD_ID = "ikzejthq1q7yt9"


def run_command(cmd, check=True):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0 and check:
        print(f"Error: {result.stderr}")
    return result.stdout.strip()


def get_infisical_secret(name):
    """Get secret from Infisical."""
    try:
        result = subprocess.run(
            f"infisical secrets get {name} --plain",
            shell=True,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            return lines[-1] if lines else None
    except Exception:
        pass
    return None


def deploy():
    api_key = get_infisical_secret("RUNPOD_API_KEY")

    if not api_key:
        print("ERROR: Could not get RUNPOD_API_KEY from Infisical")
        print("Please ensure you're logged in: infisical login")
        sys.exit(1)

    print("=== SimHPC Deployment ===\n")
    print(f"API Key: {api_key[:10]}...")

    # Build
    print("\nBuilding unified image...")
    run_command(f"docker build -f Dockerfile.unified -t {IMAGE_NAME} .", check=False)

    # Push
    print("Pushing to Docker Hub...")
    run_command(f"docker push {IMAGE_NAME}", check=False)

    # Stop
    print(f"\nStopping pod {POD_ID}...")
    stop_resp = requests.post(
        "https://api.runpod.io/graphql",
        json={"query": f'mutation {{ podStop(input: {{ podId: "{POD_ID}" }}) {{ id }} }}'},
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    print(f"Stop: {stop_resp.text}")

    print("Waiting 30s for GPU release...")
    time.sleep(30)

    # Resume
    print(f"Resuming pod {POD_ID}...")
    resume_resp = requests.post(
        "https://api.runpod.io/graphql",
        json={
            "query": f'mutation {{ podResume(input: {{ podId: "{POD_ID}", gpuCount: 1 }}) {{ id }} }}'
        },
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    print(f"Resume: {resume_resp.text}")

    print("\n=== Done ===")
    print(f"Check: https://{POD_ID}-8080.proxy.runpod.net")


if __name__ == "__main__":
    deploy()
