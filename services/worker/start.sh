#!/bin/bash
echo "🚀 Starting SimHPC v2.5.6 Unified..."

# Ensure Port 8888 is free (kills default Jupyter Lab)
fuser -k 8888/tcp || true

cd /app
export PYTHONPATH=/app
export PYTHONUNBUFFERED=1

echo "Starting FastAPI Gateway (Port 8888)..."
python3 -m uvicorn api:app --host 0.0.0.0 --port 8888 --forwarded-allow-ips='*' &

echo "Starting Physics Worker..."
python3 -u worker.py &

echo "Starting Autoscaler..."
python3 -u autoscaler.py &

wait