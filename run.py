#!/usr/bin/env python3
"""
SimHPC Entry Point with SERVICE_ROLE model.

Roles:
    api      - HTTP only (uvicorn)
    worker   - background jobs only
    unified - API + worker supervisor (dev/small cluster)

Usage:
    SERVICE_ROLE=api python run.py
    SERVICE_ROLE=worker python run.py
    SERVICE_ROLE=unified python run.py
"""

import os
import sys
import subprocess
import threading
import signal

import uvicorn
from fastapi.middleware.cors import CORSMiddleware

SERVICE_ROLE = os.getenv("SERVICE_ROLE", "api").lower()


def run_api():
    """Start API server only."""
    print(f"🚀 Starting SimHPC API (port 8080)...")

    pod_app_path = "/runpod-volume/app"
    if os.path.exists(pod_app_path):
        sys.path.append(pod_app_path)
        os.chdir(pod_app_path)
    else:
        local_worker_path = os.path.join(os.getcwd(), "services", "worker")
        if local_worker_path not in sys.path:
            sys.path.append(local_worker_path)

    try:
        from worker import app
    except ImportError as e:
        print(f"❌ Critical Error: Could not import 'app' from 'worker.py'")
        raise e

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    uvicorn.run(app, host="0.0.0.0", port=8080)


def run_worker():
    """Start worker only."""
    print(f"🔧 Starting SimHPC Worker (background)...")

    pod_app_path = "/runpod-volume/app"
    if os.path.exists(pod_app_path):
        sys.path.append(pod_app_path)
        os.chdir(pod_app_path)

    try:
        from app.services.worker.worker import process_job_loop

        process_job_loop()
    except ImportError as e:
        print(f"❌ Critical Error: Could not import worker loop: {e}")
        sys.exit(1)


def run_unified():
    """Start both API and worker (dev/small cluster)."""
    print(f"🚀 Starting SimHPC Unified (API + Worker)...")

    pod_app_path = "/runpod-volume/app"
    if os.path.exists(pod_app_path):
        sys.path.append(pod_app_path)
        os.chdir(pod_app_path)

    def api_server():
        try:
            from worker import app
        except ImportError as e:
            print(f"❌ Critical Error: Could not import 'app'")
            raise e

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
            allow_credentials=True,
        )

        uvicorn.run(app, host="0.0.0.0", port=8080)

    def worker_loop():
        try:
            from app.services.worker.worker import process_job_loop

            process_job_loop()
        except ImportError as e:
            print(f"❌ Worker Error: {e}")

    threading.Thread(target=worker_loop, daemon=True).start()
    api_server()


def handle_shutdown(signum, frame):
    print(f"⚠️ Received signal {signum}, shutting down...")
    sys.exit(0)


def main():
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    print(f"📋 SERVICE_ROLE={SERVICE_ROLE}")

    if SERVICE_ROLE == "api":
        run_api()
    elif SERVICE_ROLE == "worker":
        run_worker()
    elif SERVICE_ROLE == "unified":
        run_unified()
    else:
        print(f"❌ Invalid SERVICE_ROLE={SERVICE_ROLE}")
        print(f"Valid roles: api, worker, unified")
        sys.exit(1)


if __name__ == "__main__":
    main()
