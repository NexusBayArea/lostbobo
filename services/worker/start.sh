#!/bin/bash
set -e

echo "[SimHPC] Starting SimHPC Unified Stack (single-pod)..."

cd /app
export PYTHONPATH=/app

# Start all services in background (single-pod unified mode)
echo "[SimHPC] Launching FastAPI on port 8888..."
fuser -k 8888/tcp || true
python3 -m uvicorn api:app --host 0.0.0.0 --port 8888 --workers 1 &
API_PID=$!

echo "[SimHPC] Launching physics worker..."
python3 -u worker.py &
WORKER_PID=$!

echo "[SimHPC] Launching autoscaler..."
python3 -u autoscaler.py &
AUTOSCALER_PID=$!

echo "[SimHPC] All services started (API:$API_PID, Worker:$WORKER_PID, Autoscaler:$AUTOSCALER_PID)"

# Wait for all background processes
wait