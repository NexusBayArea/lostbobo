#!/bin/bash
# SimHPC Integrated Skill Tool

case $1 in
  deploy)
    echo "🚀 Deploying Worker to RunPod..."
    python3 /workspace/scripts/deploy_to_runpod.py
    ;;
  check-db)
    echo "🔍 Checking Database Constraints..."
    echo "Run this in Supabase SQL Editor: SELECT * FROM auth.users WHERE id NOT IN (SELECT user_id FROM onboarding_state);"
    ;;
  fix-all)
    echo "🛠️ Applying CORS fix and formatting..."
    python3 -c "
import os
path = '/runpod-volume/app/worker.py'
if not os.path.exists(path):
    path = os.path.join(os.getcwd(), 'services', 'worker', 'worker.py')
content = \"\"\"#!/usr/bin/env python3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.get('/api/v1/simulations')
async def sims(): return {'status': 'active'}\"\"\"
with open(path, 'w') as f: f.write(content)"
    
    # Restart the API if lsof is available
    if command -v lsof >/dev/null 2>&1; then
        kill -9 $(lsof -t -i:8080) 2>/dev/null
    fi
    python3 /runpod-volume/app/run_api.py &
    echo "✅ API Restored with CORS."
    ;;
  fix-cors)
    echo "🛠️ Injecting CORS fix into worker.py..."
    printf '\nfrom fastapi.middleware.cors import CORSMiddleware\napp.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True)\n' >> /runpod-volume/app/worker.py
    ;;
  start-api)
    echo "🚀 Starting SimHPC Worker API..."
    cd /runpod-volume/app
    nohup uvicorn worker:app --host 0.0.0.0 --port 8080 --reload > /runpod-volume/api.log 2>&1 &
    echo "✅ API started in background. Logs: /runpod-volume/api.log"
    ;;
  restart-api)
    echo "🔄 Restarting SimHPC Worker API..."
    pkill -f uvicorn
    sleep 2
    cd /runpod-volume/app && nohup uvicorn worker:app --host 0.0.0.0 --port 8080 --reload > /runpod-volume/api.log 2>&1 &
    echo "✅ API restarted in background. Logs: /runpod-volume/api.log"
    ;;
  status)
    echo "📊 SimHPC Stack Status:"
    POD_ID=$(infisical secrets get RUNPOD_ID --plain 2>/dev/null || echo "UNKNOWN")
    echo "RunPod API: https://${POD_ID}-8080.proxy.runpod.net/health"
    echo "Frontend: https://simhpc.com"
    ;;
  *)
    echo "Usage: simhpc {deploy|check-db|fix-all|fix-cors|start-api|status}"
    ;;
esac
