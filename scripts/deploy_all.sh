#!/bin/bash

set -e

echo "[1/6] Running Local Build Test..."
infisical run -- npm run build

if [ $? -ne 0 ]; then
    echo "Local build failed. Fix pathing/imports before pushing."
    exit 1
fi

echo "[2/6] Build passed. Syncing Infisical..."
infisical secrets push

echo "[3/6] Deploying to Vercel..."
infisical run --env=production --projectId=f8464ba0-1b93-45a1-86b5-c8ea5a81a2a4 -- vercel --prod --yes

echo "[4/6] Triggering Docker build and push to Docker Hub..."
# This will trigger the deploy.yml workflow which handles Docker login
git add . 
git commit -m "ci: trigger docker build and deploy to RunPod"
git push origin main

echo "[5/6] Waiting for GitHub Actions to complete..."
# Wait for workflow to complete
sleep 10

echo "[6/6] Triggering RunPod restart (auto-deploy-runpod workflow)..."
gh workflow run auto-deploy-runpod.yml

echo "=== Deployment Complete ==="
echo "- Vercel: https://simhpc.com"
echo "- Docker: simhpcworker/simhpc-unified:latest"
echo "- RunPod: Auto-deploy workflow triggered"