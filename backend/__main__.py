#!/usr/bin/env python3
"""
SimHPC Backend Production Entry Point
=====================================

Production-ready entrypoint using Gunicorn + Uvicorn workers.
"""

import sys
from pathlib import Path

# Ensure backend is importable when run directly
if __name__ == "__main__":
    backend_root = Path(__file__).resolve().parent
    if str(backend_root.parent) not in sys.path:
        sys.path.insert(0, str(backend_root.parent))

import multiprocessing
import os

from backend.app.main import app


def get_workers() -> int:
    """Determine optimal number of workers."""
    cpu_count = multiprocessing.cpu_count()
    return max(2, (cpu_count * 2) + 1)


def main():
    """Run SimHPC in production mode with Gunicorn."""
    print("🚀 Starting SimHPC Backend (Production Mode v3.5.1)")
    print(f"   Workers : {get_workers()}")
    print("   Host    : 0.0.0.0:8000")
    print("   Mode    : Gunicorn + Uvicorn")
    print("=" * 70)

    gunicorn_options = {
        "bind": "0.0.0.0:8000",
        "workers": get_workers(),
        "worker_class": "uvicorn.workers.UvicornWorker",
        "worker_connections": 1000,
        "timeout": 300,
        "keepalive": 65,
        "max_requests": 1000,
        "max_requests_jitter": 100,
        "loglevel": "info",
        "accesslog": "-",
        "errorlog": "-",
        "capture_output": True,
        "preload_app": True,
    }

    if os.getenv("WORKERS"):
        gunicorn_options["workers"] = int(os.getenv("WORKERS"))

    try:
        import gunicorn.app.base

        class StandaloneApplication(gunicorn.app.base.BaseApplication):
            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super().__init__()

            def load_config(self):
                for key, value in self.options.items():
                    if key in self.cfg.settings:
                        self.cfg.set(key, value)

            def load(self):
                return self.application

        StandaloneApplication(app, gunicorn_options).run()

    except ImportError:
        print("⚠️  Gunicorn not found. Falling back to Uvicorn.")
        import uvicorn

        uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Gracefully shutting down SimHPC Backend...")
    except Exception as e:
        print(f"\n❌ Failed to start backend: {e}")
        sys.exit(1)
