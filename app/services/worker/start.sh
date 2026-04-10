#!/bin/bash
set -e

trap "kill 0" SIGINT SIGTERM EXIT

echo "[SimHPC] Starting SimHPC Unified Stack (8080/8000)..."

cd /app
export PYTHONPATH=/app

# Clear ports for dual-HTTPS system
echo "[SimHPC] Clearing ports 8080, 8000..."
fuser -k 8080/tcp 2>/dev/null || true
fuser -k 8000/tcp 2>/dev/null || true

# Primary API on port 8080
echo "[SimHPC] Launching FastAPI on port 8080 (Primary)..."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --workers 1 &
API_PID_8080=$!

# Backup API on port 8000 (redundancy)
echo "[SimHPC] Launching FastAPI on port 8000 (Backup)..."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 &
API_PID_8000=$!

# Launch worker
echo "[SimHPC] Launching physics worker..."
python3 -u worker.py &
WORKER_PID=$!

# Launch autoscaler
echo "[SimHPC] Launching autoscaler..."
python3 -u autoscaler.py &
AUTOSCALER_PID=$!

echo "[SimHPC] All services started (API-8080:$API_PID_8080, API-8000:$API_PID_8000, Worker:$WORKER_PID, Autoscaler:$AUTOSCALER_PID)"

# Wait for all background processes
wait