---
name: deployment
description: Complete deployment pipeline for SimHPC - Vercel, GitHub, Docker Hub, Supabase, and RunPod.
version: 2.6.4
license: MIT
compatibility: opencode
---

# Deployment Skill Set

Complete deployment pipeline for SimHPC v2.6.4.

## Version: 2.6.4

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

## GitHub Actions Workflow (deploy.yml)

### Secrets (v2.6.4) - Strict Naming

| Secret | Value |
|--------|-------|
| `DOCKER_LOGIN` | `simhpcworker` (Docker Hub username) |
| `DOCKER_PW_TOKEN` | Docker Hub PAT |

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

## Skill 10: RunPod API Deployment (v2.6.6)

**No SSH** - We use GraphQL API to reset pods:

| Secret | Purpose | Status |
|--------|---------|--------|
| `RUNPOD_API_KEY` | GraphQL API authentication | CRITICAL |
| `RUNPOD_ID` | Pod identifier for podReset | CRITICAL |

### Lean Secret List (v2.6.6)

Only these secrets are needed for the API-only deployment pipeline:

| Secret | Purpose | Status |
|--------|---------|--------|
| `RUNPOD_API_KEY` | podReset mutation | CRITICAL |
| `RUNPOD_ID` | Which pod to reset | CRITICAL |
| `DOCKER_LOGIN` | Docker Hub username | CRITICAL |
| `DOCKER_PW_TOKEN` | Docker Hub PAT | CRITICAL |

**Delete these if present:**
- `RUNPOD_SSH_KEY` - Not needed (API-only deploy)
- `RUNPOD_JUPYTER_PW` - Not used (custom Dockerfile)
- `RUNPOD_USERNAME` - Not needed (API-only deploy)

## Skill 11: RunPod Ground Truth (v2.6.6)

**API Key**: `RUNPOD_API_KEY` - Use for GraphQL mutations
**Pod Identifier**: `RUNPOD_ID` - The pod to reset/pull fresh image
**Automation**: We deploy via API `podReset` - forces fresh docker pull

## Skill 12: Pod Reset vs Restart

| Action | Effect | Use Case |
|--------|--------|----------|
| `podRestart` | Reboots container, uses cached image | Quick debug |
| `podReset` | Wipes container, pulls fresh image | **CI/CD deployments (REQUIRED)** |

**Why podReset**: `podRestart` won't pull new Docker image layers — only `podReset` triggers a fresh `docker pull`.

## Quick Start

```bash
# Push to main triggers:
# 1. Build & push simhpcworker/simhpc-unified:latest
# 2. podReset to pull fresh image
git push origin main
```

## Deployment Flow

```
┌─────────────────┐
│  Push to GitHub │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Build Matrix   │ ──→ worker, api, autoscaler (parallel)
│  (Docker)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Push Images    │ ──→ SHA + latest tags
│  (Docker Hub)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Deploy RunPod  │ ──→ API reset (podReset)
 │  (podReset)    │
└─────────────────┘
```

## GitHub Actions Workflow

### Docker Build (Parallel)

```yaml
- name: Build & Push Image
  run: |
    docker build \
      -f Dockerfile.unified \
      -t simhpcworker/simhpc-unified:latest \
      -t simhpcworker/simhpc-unified:${{ github.sha }} \
      .
    docker push simhpcworker/simhpc-unified:latest
```

### RunPod Deploy (API)

```yaml
- name: Deploy to RunPod (API)
  run: |
    response=$(curl -s -X POST "https://api.runpod.io/graphql" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $RUNPOD_API_KEY" \
      -d "{\"query\": \"mutation { podReset(input: { podId: \\\"$RUNPOD_ID\\\" }) { id status } }\"}")
```

## Dockerfile Paths

| Image | Dockerfile |
|-------|------------|
| simhpc-unified | `Dockerfile.unified` |
| simhpc-worker | `Dockerfile.worker` |
| simhpc-autoscaler | `Dockerfile.autoscaler` |

## Examples

- "Build and push the unified image to Docker Hub"
- "Deploy a new GPU pod to RunPod"
- "Sync new pod metadata to Infisical and Vercel"