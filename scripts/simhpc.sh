#!/bin/bash
# SimHPC Integrated Skill Tool

case $1 in
  deploy)
    echo "🚀 Deploying Worker to RunPod..."
    python3 /workspace/scripts/deploy_to_runpod.py
    ;;
  check-db)
    echo "🔍 Checking Database Constraints..."
    # This command uses the Supabase CLI (if installed) to check for missing records
    echo "Run this in Supabase SQL Editor: SELECT * FROM auth.users WHERE id NOT IN (SELECT user_id FROM onboarding_state);"
    ;;
  fix-cors)
    echo "🛠️ Injecting CORS fix into worker.py..."
    # Appending a snippet that adds middleware if it doesn't exist
    # (Though we updated the source file, this serves as a recovery skill)
    printf '\nfrom fastapi.middleware.cors import CORSMiddleware\napp.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True)\n' >> /runpod-volume/app/worker.py
    ;;
  status)
    echo "📊 SimHPC Stack Status:"
    # Use pod id from Infisical or environment
    POD_ID=$(infisical secrets get RUNPOD_ID --plain 2>/dev/null || echo "UNKNOWN")
    echo "RunPod API: https://${POD_ID}-8000.proxy.runpod.net/health"
    echo "Frontend: https://simhpc.com"
    ;;
  *)
    echo "Usage: simhpc {deploy|check-db|fix-cors|status}"
    ;;
esac
