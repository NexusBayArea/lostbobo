import uvicorn
import os
import sys
from fastapi.middleware.cors import CORSMiddleware

# Setup for SimHPC
# Ensure we check the current directory and potential /runpod-volume/app
pod_app_path = "/runpod-volume/app"
if os.path.exists(pod_app_path):
    sys.path.append(pod_app_path)
    os.chdir(pod_app_path)
else:
    # Fallback for local development
    local_worker_path = os.path.join(os.getcwd(), "services", "worker")
    if local_worker_path not in sys.path:
        sys.path.append(local_worker_path)

# This ensures the app object has CORS before starting
try:
    from worker import app
except ImportError as e:
    print(
        f"❌ Critical Error: Could not import 'app' from 'worker.py'. Path: {sys.path}"
    )
    raise e

# Force add CORS middleware just in case
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

if __name__ == "__main__":
    print("🚀 Starting SimHPC Worker API (Port 8080)...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
