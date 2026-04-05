#!/usr/bin/env python3
"""
SimHPC RunPod Deployment Script

Automates the full deployment pipeline:
1. Build and push Docker images to Docker Hub
2. Restart RunPod pod to pull latest images

Usage:
    python scripts/deploy_worker.py

Requires:
    - pip install runpod docker
    - Infisical CLI installed and authenticated
    - RUNPOD_API_KEY and RUNPOD_ID in Infisical (prod environment)
"""

import os
import sys
import json
import subprocess
import runpod


def run_command(cmd, shell=True, check=True):
    """Run a shell command and return output."""
    print(f"Running: {cmd}")
    result = subprocess.run(
        cmd, shell=shell, capture_output=True, text=True, check=check
    )
    if result.stdout:
        print(result.stdout)
    if result.stderr and result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
    return result


def get_infisical_secrets(*keys):
    """Fetch secrets from Infisical prod environment."""
    secrets = {}
    for key in keys:
        result = subprocess.run(
            f"infisical secrets get {key} --plain",
            shell=True,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            # Get value from stdout (stderr contains "new release" message)
            value = result.stdout.strip()
            secrets[key] = value
        else:
            print(f"Warning: Could not fetch {key} from Infisical")
    return secrets


def build_and_push_images():
    """Build and push worker and autoscaler images to Docker Hub."""
    print("\n=== Building Docker images ===")

    # Build worker image
    print("Building worker image...")
    run_command(
        "docker build -f Dockerfile.worker -t simhpcworker/simhpc-worker:latest ."
    )
    run_command("docker push simhpcworker/simhpc-worker:latest")

    # Build autoscaler image
    print("Building autoscaler image...")
    run_command(
        "docker build -f Dockerfile.autoscaler -t simhpcworker/simhpc-autoscaler:latest ."
    )
    run_command("docker push simhpcworker/simhpc-autoscaler:latest")

    print("Docker images pushed successfully!")


def restart_pod(api_key, pod_id):
    """Restart RunPod pod to pull latest images."""
    print(f"\n=== Restarting pod {pod_id} ===")

    runpod.api_key = api_key

    # Stop the pod
    print("Stopping pod...")
    stop_result = runpod.stop_pod(pod_id)
    print(f"Stop result: {stop_result}")

    # Resume the pod
    print("Resuming pod...")
    resume_result = runpod.resume_pod(pod_id, gpu_count=1)
    print(f"Resume result: {resume_result}")

    print("Pod restarted successfully!")


def deploy():
    """Main deployment function."""
    print("=== SimHPC RunPod Deployment ===")

    # Get secrets from Infisical
    print("\nFetching secrets from Infisical...")
    secrets = get_infisical_secrets("RUNPOD_API_KEY", "RUNPOD_ID")

    if not secrets.get("RUNPOD_API_KEY"):
        print("Error: RUNPOD_API_KEY not found in Infisical")
        sys.exit(1)

    if not secrets.get("RUNPOD_ID"):
        print("Error: RUNPOD_ID not found in Infisical")
        sys.exit(1)

    print(f"Got RUNPOD_ID: {secrets['RUNPOD_ID']}")

    # Build and push images
    build_and_push_images()

    # Restart pod
    restart_pod(secrets["RUNPOD_API_KEY"], secrets["RUNPOD_ID"])

    print("\n=== Deployment complete ===")


if __name__ == "__main__":
    deploy()
