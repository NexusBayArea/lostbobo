import os
import time

import requests
from loguru import logger

IDLE_TIMEOUT_SECONDS = 1800
CHECK_INTERVAL = 60
ACTIVITY_FILE = "/tmp/last_active.txt"
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
POD_ID = os.getenv("RUNPOD_POD_ID")


def get_last_activity():
    try:
        with open(ACTIVITY_FILE) as f:
            return float(f.read().strip())
    except Exception:
        return time.time()


def stop_self():
    logger.warning("Inactivity threshold met. Shutting down pod...")
    url = f"https://api.runpod.io/v2/{POD_ID}/stop"
    headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}"}

    try:
        response = requests.post(url, headers=headers, timeout=30)
        logger.info(f"RunPod response: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to send stop signal: {e}")


if __name__ == "__main__":
    logger.info("Auto-shutdown monitor started.")
    with open(ACTIVITY_FILE, "w") as f:
        f.write(str(time.time()))

    while True:
        last_active = get_last_activity()
        idle_time = time.time() - last_active

        if idle_time > IDLE_TIMEOUT_SECONDS:
            stop_self()
            break

        time.sleep(CHECK_INTERVAL)
