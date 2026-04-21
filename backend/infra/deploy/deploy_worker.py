#!/usr/bin/env python3
"""
SimHPC RunPod Deployment Script

Automates the full deployment pipeline:
1. Build and push Docker images to Docker Hub
2. Fetch secrets from Infisical
3. Recreate RunPod pod with env vars from Infisical

Usage:
    python scripts/deploy_worker.py

Requires:
    - pip install runpod
    - Infisical CLI installed and authenticated
    - All required secrets in Infisical
"""

import subprocess
import sys

import runpod

INFISICAL_CLIENT_ID = "5d322bca-5770-4071-b059-98b0f56fcc6d"
INFISICAL_CLIENT_SECRET = "be05f79075ebfea520463f6e223bcac61ab547d43310ad6636070b73c023d8f7"
INFISICAL_PROJECT_ID = "f8464ba0-1b93-45a1-86b5-c8ea5a81a2a4"

# Infisical to script name mapping
SECRET_MAPPING = {
    "RUNPOD_API_KEY": "RUNPOD_API_KEY",
    "RUNPOD_ID": "RUNPOD_ID",
    "REDIS_URL": "REDIS_URL",
    "MERCURY_API_KEY": "MERCURY_API_KEY",
    "SB_URL": "SB_URL",
    "SUPABASE_SERVICE_ROLE_KEY": "SB_SECRET_KEY",
    "SUPABASE_JWT_SECRET": "SB_JWT_SECRET",
    "SUPABASE_ANON_KEY": "VITE_SUPABASE_ANON",
}

REQUIRED_SECRETS = list(SECRET_MAPPING.keys())


def run_command(cmd, shell=True, check=True):
    """Run a shell command and return output."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, check=check)
    if result.stdout:
        print(result.stdout)
    if result.stderr and result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
    return result


def get_infisical_secrets(*keys):
    """Fetch secrets from Infisical using machine identity."""
    secrets = {}
    for key in keys:
        infisical_name = SECRET_MAPPING.get(key, key)
        cmd = f"set INFISICAL_CLIENT_ID={INFISICAL_CLIENT_ID}&& set INFISICAL_CLIENT_SECRET={INFISICAL_CLIENT_SECRET}&& infisical secrets get {infisical_name} --projectId={INFISICAL_PROJECT_ID} --plain"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            value = result.stdout.strip()
            if value and "not found" not in value.lower():
                secrets[key] = value
                print(f"  Got {key}: {'*' * 8}")
            else:
                print(f"Warning: {key} not found in Infisical")
        else:
            print(f"Warning: Could not fetch {key} from Infisical: {result.stderr}")
    return secrets


def build_and_push_images():
    """Build and push worker, autoscaler, and API images to Docker Hub."""
    print("\n=== Building Docker images ===")

    print("Building worker image...")
    run_command("docker build -f Dockerfile.worker -t simhpcworker/simhpc-worker:latest .")
    run_command("docker push simhpcworker/simhpc-worker:latest")

    print("Building autoscaler image...")
    run_command("docker build -f Dockerfile.autoscaler -t simhpcworker/simhpc-autoscaler:latest .")
    run_command("docker push simhpcworker/simhpc-autoscaler:latest")

    print("Building API image...")
    run_command("docker build -f Dockerfile.api -t simhpcworker/simhpc-api:latest .")
    run_command("docker push simhpcworker/simhpc-api:latest")

    print("Docker images pushed successfully!")


def recreate_pod(api_key, pod_id, env_vars):
    """Terminate old pod and create new one with env vars."""
    print(f"\n=== Recreating pod {pod_id} ===")

    runpod.api_key = api_key

    # Terminate old pod
    print("Terminating old pod...")
    runpod.terminate_pod(pod_id)

    # Create new pod with env vars
    print("Creating new pod with env vars from Infisical...")
    pod = runpod.create_pod(
        name="simhpc-worker",
        image_name="simhpcworker/simhpc-worker:latest",
        gpu_type_id="NVIDIA A40",
        gpu_count=1,
        volume_in_gb=20,
        container_disk_in_gb=20,
        ports="8080/http,22/tcp",
        env=env_vars,
    )
    new_pod_id = pod["id"]
    print(f"New pod created: {new_pod_id}")

    # Update RUNPOD_ID in Infisical
    print("Updating RUNPOD_ID in Infisical...")
    cmd = f"set INFISICAL_CLIENT_ID={INFISICAL_CLIENT_ID}&& set INFISICAL_CLIENT_SECRET={INFISICAL_CLIENT_SECRET}&& infisical secrets set RUNPOD_ID={new_pod_id} --projectId={INFISICAL_PROJECT_ID}"
    subprocess.run(cmd, shell=True, capture_output=True)

    return new_pod_id


def deploy():
    """Main deployment function."""
    print("=== SimHPC RunPod Deployment ===")

    # Get all secrets from Infisical
    print("\nFetching secrets from Infisical...")
    secrets = get_infisical_secrets(*REQUIRED_SECRETS)

    for key in REQUIRED_SECRETS:
        if not secrets.get(key):
            print(f"Error: {key} not found in Infisical")
            sys.exit(1)

    # Build and push images
    build_and_push_images()

    # Prepare env vars for pod
    env_vars = {
        "REDIS_URL": secrets["REDIS_URL"],
        "MERCURY_API_KEY": secrets["MERCURY_API_KEY"],
        "SB_URL": secrets["SB_URL"],
        "SUPABASE_SERVICE_ROLE_KEY": secrets["SUPABASE_SERVICE_ROLE_KEY"],
        "SUPABASE_JWT_SECRET": secrets.get("SUPABASE_JWT_SECRET", ""),
        "SUPABASE_ANON_KEY": secrets.get("SUPABASE_ANON_KEY", ""),
        "RUNPOD_ID": secrets.get("RUNPOD_ID", ""),
    }

    # Recreate pod with env vars
    new_pod_id = recreate_pod(secrets["RUNPOD_API_KEY"], secrets["RUNPOD_ID"], env_vars)

    print("\n=== Worker deployment complete ===")
    print(f"Worker pod: {new_pod_id}")


if __name__ == "__main__":
    deploy()
