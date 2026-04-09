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

## Skill 10: RunPod API Deployment (v2.6.4)

**No SSH** - We use GraphQL API to restart pods:

| Secret | Purpose |
|--------|---------|
| `RUNPOD_API_KEY` | GraphQL API authentication |
| `RUNPOD_ID` | Pod identifier |

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

## Skill 12: RunPod Ground Truth (v2.6.4)

**API Key**: `RUNPOD_API_KEY` - Use for GraphQL/Python scripts
**Pod Identifier**: `RUNPOD_ID` - Never use `RUNPOD_POD_ID`
**SSH**: `RUNPOD_SSH`, `RUNPOD_TCP_PORT_22` - Only if using SSH deployment
**Automation**: We deploy via API `podRestart` - no SSH keys needed

## Skill 13: Port Precision (v2.6.4)
- **SSH Port**: Always use `${{ secrets.RUNPOD_TCP_PORT_22 }}`
- **Validation**: Never hardcode `22` - pull from Infisical
- **Note**: We use API restart (`auto-deploy-runpod.yml`) instead of SSH

## Quick Start

Use the master deploy script for one-click deployment:

```bash
bash scripts/deploy_all.sh
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
│  Deploy RunPod  │ ──→ API restart (no SSH)
│  (podRestart)  │
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
      -d "{\"query\": \"mutation { podRestart(podId: \\"$RUNPOD_ID\\") { id status } }\"}")
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