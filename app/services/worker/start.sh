#!/bin/bash
set -e

echo "[SimHPC] Booting unified stack..."

cd /app
export PYTHONPATH=/app

# Kill stale ports
fuser -k 8080/tcp || true
fuser -k 8000/tcp || true

# Start API
echo "[SimHPC] Starting API (8080)..."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080 &
API_PID=$!

# Start worker
echo "[SimHPC] Starting worker..."
python3 -u app/services/worker/worker.py &
WORKER_PID=$!

# Start autoscaler
echo "[SimHPC] Starting autoscaler..."
python3 -u app/services/worker/autoscaler.py &
AUTO_PID=$!

# Monitor processes (CRITICAL)
while true; do
    if ! kill -0 $API_PID 2>/dev/null; then
        echo "[FATAL] API crashed"
        exit 1
    fi
    if ! kill -0 $WORKER_PID 2>/dev/null; then
        echo "[FATAL] Worker crashed"
        exit 1
    fi
    if ! kill -0 $AUTO_PID 2>/dev/null; then
        echo "[FATAL] Autoscaler crashed"
        exit 1
    fi
    sleep 5
done