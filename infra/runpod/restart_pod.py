#!/usr/bin/env python3
"""
Update/Restart RunPod Pod
"""

import os
import runpod

API_KEY = os.getenv("RUNPOD_API_KEY")
if not API_KEY:
    raise ValueError("RUNPOD_API_KEY not set")

runpod.api_key = API_KEY

POD_ID = os.getenv("RUNPOD_POD_ID", "q41n3g4zwr84wt")

print(f"Stopping pod {POD_ID}...")
runpod.stop_pod(POD_ID)

print("Waiting for pod to stop...")
import time

time.sleep(5)

print(f"Starting pod {POD_ID}...")
runpod.start_pod(POD_ID)

print(f"Pod {POD_ID} restarted - will pull new image")
