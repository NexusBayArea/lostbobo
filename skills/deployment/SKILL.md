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

echo "[1/4] Syncing to GitHub..."
git add . 
git commit -m "ci: trigger docker build and deploy to RunPod"
git push origin main

echo "[2/4] Waiting for Docker build..."
sleep 30

echo "[3/4] Deploying to RunPod..."
gh workflow run auto-deploy-runpod.yml

echo "[4/4] Deployment triggered."
```

## GitHub Actions Workflow (deploy.yml)

**Critical: Use ONLY these secret names (v2.6.4)**

| Secret | Value |
|--------|-------|
| `DOCKER_LOGIN` | `simhpcworker` (Docker Hub username) |
| `DOCKER_PW_TOKEN` | Docker Hub PAT (Personal Access Token) |

```yaml
- name: Login to Docker Hub
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKER_LOGIN }}
    password: ${{ secrets.DOCKER_PW_TOKEN }}
```

### Rules (v2.6.4)

- **DO NOT** use `DOCKER_USERNAME` or `DOCKER_PASSWORD`
- **ALWAYS** use `DOCKER_LOGIN` for username
- **ALWAYS** use `DOCKER_PW_TOKEN` for PAT
- **NO** Infisical CLI in YAML - secrets sync natively via GitHub App

## Skill 10: SSH Deployment Logic

| Secret | Purpose |
|--------|---------|
| `SSH_HOST` | Remote IP of the GPU/A40 instance |
| `SSH_USERNAME` | SSH username (usually `root`) |
| `SSH_PRIVATE_KEY` | Ed25519 or RSA private key for passwordless entry |

```yaml
- name: Deploy to RunPod via SSH
  uses: appleboy/ssh-action@v1.0.3
  with:
    host: ${{ secrets.SSH_HOST }}
    username: ${{ secrets.SSH_USERNAME }}
    key: ${{ secrets.SSH_PRIVATE_KEY }}
    port: 22
    script: |
      docker pull simhpcworker/simhpc-unified:latest
      docker stop simhpc-unified || true
      docker rm simhpc-unified || true
      docker run -d --name simhpc-unified --gpus all simhpcworker/simhpc-unified:latest
```

### Required Infisical Secrets for SSH

```bash
infisical secrets set SSH_HOST="[YOUR_SERVER_IP]"
infisical secrets set SSH_USERNAME="root"
infisical secrets set SSH_PRIVATE_KEY="[PASTE_YOUR_PRIVATE_KEY]"
```

## Skill 11: RunPod Infrastructure Constraints (v2.6.4)

**NO HALLUCINATIONS**: Use only these exact key names from Infisical:

| Service | Infisical Key | GitHub Action Reference |
|---------|---------------|------------------------|
| Auth | `RUNPOD_API_KEY` | `${{ secrets.RUNPOD_API_KEY }}` |
| Auth | `RUNPOD_USERNAME` | `${{ secrets.RUNPOD_USERNAME }}` |
| Network | `RUNPOD_ID` | `${{ secrets.RUNPOD_ID }}` |
| Network | `RUNPOD_SSH` | `${{ secrets.RUNPOD_SSH }}` |
| Network | `RUNPOD_TCP_PORT_22` | `${{ secrets.RUNPOD_TCP_PORT_22 }}` |
| Network | `RUNPOD_HTTPS` | `${{ secrets.RUNPOD_HTTPS }}` |
| SSH Key | `RUNPOD_SSH_KEY` | `${{ secrets.RUNPOD_SSH_KEY }}` |

**Rules:**
- **DO NOT** use `SSH_HOST`, `VITE_API_URL`, or `RUNPOD_POD_ID`
- **USE** `RUNPOD_SSH` for SSH address and `RUNPOD_TCP_PORT_22` for port
- All values must be in Infisical and synced via GitHub App

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
