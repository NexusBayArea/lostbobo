#!/usr/bin/env python3
import sys
import subprocess
import requests
import time

IMAGE_NAME = "simhpcworker/simhpc-unified:latest"
POD_ID = "ikzejthq1q7yt9"


def run_command(cmd, check=True):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0 and check:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()


def get_secret(name):
    try:
        cmd = f"infisical secrets get {name} --plain"
        val = run_command(cmd)
        return val.split("\n")[-1]
    except:
        return None


def deploy():
    print("=== SimHPC Deployment ===\n")

    api_key = get_secret("RUNPOD_API_KEY")

    # Build and Push
    print("Building & pushing unified image...")
    run_command(f"docker build -f Dockerfile.unified -t {IMAGE_NAME} .")
    run_command(f"docker push {IMAGE_NAME}")

    # Stop then Resume to force fresh image pull
    print(f"\nStopping pod {POD_ID}...")
    stop_resp = requests.post(
        "https://api.runpod.io/graphql",
        json={
            "query": f'mutation {{ podStop(input: {{ podId: "{POD_ID}" }}) {{ id }} }}'
        },
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    print(f"Stop response: {stop_resp.text}")

    print("Waiting 30s for GPU release...")
    time.sleep(30)

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
    print(f"Resume response: {resume_resp.text}")

    print("\nDeployment complete!")
    print(f"API URL: https://{POD_ID}-8080.proxy.runpod.net")


if __name__ == "__main__":
    deploy()
