import os

import requests


def update_runpod_template():
    api_key = os.getenv("RUNPOD_API_KEY")
    template_id = os.getenv("RUNPOD_TEMPLATE")
    image_name = "ghcr.io/lostbobo/simhpc_unified:latest"

    if not api_key or not template_id:
        print("RUNPOD_API_KEY or RUNPOD_TEMPLATE not set")
        return

    url = f"https://api.runpod.io/v1/templates/{template_id}"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    data = {
        "imageName": image_name,
        "containerDiskInGb": 50,
        "volumeInGb": 20,
        "ports": "8080/http,22/tcp",
        "env": {"RUNPOD_API_KEY": api_key, "IDLE_TIMEOUT_SECONDS": "1800"},
    }

    response = requests.post(url, json=data, headers=headers, timeout=30)
    if response.status_code == 200:
        print(f"Successfully updated RunPod template: {template_id}")
    else:
        print(f"Failed to update template: {response.text}")


if __name__ == "__main__":
    update_runpod_template()
