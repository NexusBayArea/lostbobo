#!/bin/bash
echo "🚀 Starting SimHPC v2.5.3 Gateway (Port 8000)..."
# Start the FastAPI API in the background
uvicorn worker:app --host 0.0.0.0 --port 8000 &

echo "⚙️ Starting SimHPC Physics Worker..."
# Start the Worker Loop in the foreground
python3 -u worker.py
