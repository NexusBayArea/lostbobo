---
name: deployment
description: Complete deployment pipeline for SimHPC - Vercel, GitHub, Docker Hub, Supabase, and RunPod.
version: 2.5.6
license: MIT
compatibility: opencode
---

# Deployment Skill Set

Complete deployment pipeline for SimHPC v2.5.6.

## Version: 2.5.6

## Docker Images

All images pushed to Docker Hub:

| Image | Tag | Purpose |
| :--- | :--- | :--- |
| simhpcworker/simhpc-unified | latest | Combined API + Worker + Autoscaler (Port 8888) |
| simhpcworker/simhpc-worker | latest | GPU physics worker |
| simhpcworker/simhpc-api | latest | FastAPI orchestrator |
| simhpcworker/simhpc-autoscaler | latest | RunPod autoscaler |

## Supabase Keys (SB Prefix)

**Important**: Infisical doesn't allow "SUPABASE" in key names. Use SB_ prefix:

| Infisical Key | Mapped To |
|--------------|-----------|
| SB_URL | VITE_SUPABASE_URL / SUPABASE_URL |
| SB_ANON_KEY | VITE_SUPABASE_ANON_KEY / SUPABASE_ANON_KEY |
| SB_SERVICE_ROLE_KEY | SUPABASE_SERVICE_ROLE_KEY |
| SB_PROJECT_ID | Supabase project ref |

## Quick Start

Use the master deploy script for one-click deployment:

```bash
bash scripts/deploy_all.sh
```

## Master Script (deploy_all.sh)

```bash
#!/bin/bash

set -e

echo "[1/6] Running Local Build Test..."
infisical run -- npm run build

echo "[2/6] Build passed. Syncing Infisical..."
infisical secrets push

echo "[3/6] Deploying to Vercel..."
infisical run --env=production --projectId=f8464ba0-1b93-45a1-86b5-c8ea5a81a2a4 -- vercel --prod --yes

echo "[4/6] Triggering Docker build..."
git add . 
git commit -m "ci: trigger docker build and deploy to RunPod"
git push origin main

echo "[5/6] Triggering RunPod restart..."
gh workflow run auto-deploy-runpod.yml

echo "=== Deployment Complete ==="
```

## GitHub Actions Workflow (deploy.yml)

The workflow now fetches Docker credentials from Infisical before logging in:

```yaml
- name: Install Infisical CLI
  run: |
    curl -1sLf 'https://dl.cloudsmith.io/public/infisical/infisical-cli/setup.deb.sh' | sudo -E bash
    sudo apt-get update
    sudo apt-get install infisical -y

- name: Export Docker credentials from Infisical
  env:
    INFISICAL_TOKEN: ${{ secrets.INFISICAL_TOKEN }}
    INFISICAL_PROJECT_ID: f8464ba0-1b93-45a1-86b5-c8ea5a81a2a4
  run: |
    eval "$(infisical export --env=production --format=export)"
    echo "DOCKER_USER=$DOCKER_USERNAME" >> $GITHUB_ENV
    echo "DOCKER_PASS=$DOCKER_PASSWORD" >> $GITHUB_ENV

- name: Login to Docker Hub
  uses: docker/login-action@v3
  with:
    username: ${{ env.DOCKER_USER }}
    password: ${{ env.DOCKER_PASS }}
```

### Required GitHub Secrets

| Secret | Source |
|--------|--------|
| `INFISICAL_TOKEN` | Infisical → Settings → Machine Identity |
| `INFISICAL_PROJECT_ID` | f8464ba0-1b93-45a1-86b5-c8ea5a81a2a4 |

### Required Infisical Secrets

| Key | Purpose |
|-----|---------|
| `DOCKER_USERNAME` | Docker Hub username |
| `DOCKER_PASSWORD` | Docker Hub password/token |

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
