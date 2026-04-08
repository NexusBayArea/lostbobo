#!/bin/bash
set -e

echo "[1/3] Local Build Test..."
npm run build

echo "[2/3] Syncing to GitHub..."
git add .
git commit -m "ci: deploy SimHPC v2.5.6 via native sync"
git push origin main

echo "[3/3] Triggering RunPod via GitHub Action..."
gh workflow run auto-deploy-runpod.yml

echo "=== Deployment Complete ==="