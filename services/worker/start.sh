#!/bin/bash
echo "🚀 Starting SimHPC v2.5.3 Gateway (Non-Root User)..."
# Start the FastAPI API
uvicorn worker:app --host 0.0.0.0 --port 8000 &

echo "⚙️ Starting SimHPC Physics Worker..."
# Start the Worker Loop
python3 -u worker.py
