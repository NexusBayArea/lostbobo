#!/bin/bash
set -e

echo "🚀 [SimHPC] Starting Unified Pod - Beta Foundation ($(date))"

# Clear any stale port binding
fuser -k 8080/tcp || true

echo "Starting FastAPI server on 0.0.0.0:8080..."

# Direct start - most reliable for debugging
exec python3 -m uvicorn api:app \
    --host 0.0.0.0 \
    --port 8080 \
    --workers 2 \
    --log-level info