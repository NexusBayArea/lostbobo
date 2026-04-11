#!/bin/bash
set -e

echo "🚀 [SimHPC] Starting API directly on port 8080 (debug mode)"

# Clear port just in case
fuser -k 8080/tcp || true

# Start API directly — this is the most reliable way to see errors
exec python3 -m uvicorn app.api.api:app --host 0.0.0.0 --port 8080 --log-level info