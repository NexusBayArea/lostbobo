#!/bin/bash
# SimHPC RunPod Setup Script (Unified)

# 1. Update and install basic dependencies
apt-get update && apt-get install -y --no-install-recommends 
    build-essential curl python3-pip python3-venv 
    && rm -rf /var/lib/apt/lists/*

# 2. Install Python requirements (Pytorch image usually has pip)
# Ensure we are in the project root
pip install fastapi uvicorn numpy pydantic

# 3. Check for the frontend dist folder
if [ ! -d "app/dist" ]; then
    echo "Frontend 'dist' folder not found. Please ensure it's uploaded to 'app/dist'."
    exit 1
fi

# 4. Start the unified service on port 8000
# RunPod's proxy expects port 8000 to be open
python3 robustness-orchestrator/run_with_cors.py
