---
name: deployment
description: Complete deployment pipeline for SimHPC - Vercel, GitHub, and unified stack deployment.
version: 2.5.4
license: MIT
compatibility: opencode
---

# Deployment Skill Set

Complete deployment pipeline for SimHPC v2.5.4.

## Version: 2.5.4

## Quick Start

Use the master deploy script for one-click deployment:

```bash
bash scripts/deploy_all.sh
```

## Master Script (deploy_all.sh)

```bash
#!/bin/bash

echo "[1/4] Syncing Infisical Secrets..."
infisical secrets push

echo "[2/4] Deploying to Vercel (Production)..."
infisical run --env=production -- vercel --prod --yes

echo "[3/4] Updating GitHub Repository..."
git add .
git commit -m "chore: production deploy v2.5.4 unified plane"
git push origin main

echo "[4/4] Fleet Synchronized."
```

## Skills Overview

### 1. Vercel Deploy
See: `vercel-deploy.md`

Deploy frontend with Infisical secret injection.

### 2. GitHub Safe Push
See: `github-safe-push.md`

Secure push with secret scanning and linting.

### 3. Supabase Sync
See: `supabase-sync.md`

Sync SB_ secrets to VITE_SUPABASE_ for Vercel.

## Deployment Flow

```
┌─────────────────┐
│  Sync Infisical  │ ← Push latest secrets
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Sync SB Secrets │ ← Rename SB_ to VITE_SUPABASE_
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Deploy to Vercel │ ← Production build
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Git Push      │ ← Safe push with scan
└─────────────────┘
```

## Manual Steps

### Deploy RunPod (Separate)

```bash
# Build unified image
docker build -f Dockerfile.unified -t simhpcworker/simhpc-unified:latest .

# Push to Docker Hub
docker push simhpcworker/simhpc-unified:latest

# Deploy to RunPod
python scripts/deploy_unified.py
```

### Update Vercel API URL

```bash
echo "https://{POD_ID}-8000.proxy.runpod.net" | vercel env add VITE_API_URL production
vercel --prod --yes
```

## Examples

- "Deploy to Vercel with Infisical secrets"
- "Safe push to GitHub with secret scan"
- "Run the full deploy_all script"
