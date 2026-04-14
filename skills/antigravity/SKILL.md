---
name: antigravity
description: Infisical-based secret management, Docker lifecycle skills, and deployment SOP for v2.5.3.
license: MIT
compatibility: opencode

> **Note**: This file is for documentation only. DO NOT PUSH TO GIT.
---

# Antigravity Infisical Skill Set

Three core skills for transitioning from local `.env` files to secret injection, plus the push/deploy workflow.

## Version: 2.5.3

## Skill 1: The Infisical Handshake

Initializes the project and connects to your environment.

### Commands

**Linux/macOS:**
```bash
infisical login
infisical init
echo "✅ Antigravity Security: Connected to v2.5.3 Secret Vault."
```

**Windows PowerShell:**
```powershell
infisical login
infisical init
Write-Host "✅ Antigravity Security: Connected to v2.5.3 Secret Vault."
```

## Skill 2: The Secret-Safe Build

Builds Docker without needing local `.env` files.

### Commands

**Linux/macOS:**
```bash
infisical run -- env | grep -v "_gitignore" > .env.tmp && \
docker-compose build --no-cache && \
rm .env.tmp && \
echo "✅ Antigravity Build: v2.5.3 image built without persistent .env."
```

**Windows PowerShell:**
```powershell
infisical run -- cmd /c "set" | Select-String -NotMatch "_gitignore" | ForEach-Object { $_.Line } | Out-File -Encoding utf8 .env.tmp
docker-compose build --no-cache
Remove-Item .env.tmp
Write-Host "✅ Antigravity Build: v2.5.3 image built without persistent .env."
```

## Skill 3: The Runtime Injector

Starts the Local Alpha Stack with secrets injected directly into memory.

### Commands

**Linux/macOS:**
```bash
infisical run -- docker-compose up
```

**Windows PowerShell:**
```powershell
infisical run -- docker-compose up
```

## Skill 4: The Deep Prune

Clears absolute everything to prevent Docker bloat.

### Commands

**Linux/macOS:**
```bash
docker system prune -a --volumes -f && \
docker builder prune -a -f && \
echo "✅ Antigravity Maintenance: Disk bloat purged."
```

**Windows PowerShell:**
```powershell
docker system prune -a --volumes -f
docker builder prune -a -f
Write-Host "✅ Antigravity Maintenance: Disk bloat purged."
```

## Push & Deploy SOP

### Quick Deploy (All Services)

```bash
# 1. Lint check
ruff check services/worker/worker.py
ruff format --check services/worker/worker.py

# 2. Commit and push
git add -A && git commit -m "v2.5.3 release" && git push origin main
```

**What happens:**
| Component | Trigger | Result |
|---|---|---|
| Frontend | Push to `main` | Vercel auto-deploys |
| Worker | `services/worker/**` or `Dockerfile.worker` | GitHub Actions → Docker Hub → Auto-restarts RunPod |
| Autoscaler | `services/worker/runpod_api.py`, `autoscaler.py`, `Dockerfile.autoscaler` | GitHub Actions → Docker Hub → Auto-restarts RunPod |

### Manual Deploy (Worker)

```bash
docker build -f Dockerfile.worker -t simhpcworker/simhpc-worker:latest .
docker push simhpcworker/simhpc-worker:latest
```

### Manual Deploy (Autoscaler)

```bash
docker build -f Dockerfile.autoscaler -t simhpcworker/simhpc-autoscaler:latest .
docker push simhpcworker/simhpc-autoscaler:latest
```

### Manual Deploy (RunPod)

All secrets fetched from Infisical (no hardcoded keys):

```bash
# Via GitHub Actions - go to Actions > Deploy to RunPod > Run workflow
# Or use the API (key from Infisical):
curl -X POST "https://api.runpod.io/graphql" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -d '{"query": "mutation { podReset(input: { podId: \"$RUNPOD_POD_ID\" }) { id status } }"}'
```

**Required Infisical Secrets:**
- `RUNPOD_API_KEY`
- `RUNPOD_POD_ID`

**Required GitHub Secrets:**
- `INFISICAL_TOKEN` (from Infisical → Settings → Access Tokens)

## Skill 4: The Secret Handshake (v2.5.12)

Whenever a new RunPod template is created, the `INFISICAL_TOKEN` must be the first variable added. This allows the `CMD` in your Dockerfile to successfully "unlock" the vault and retrieve the `REDIS_URL`, `SUPABASE_KEY`, and `ADMIN_SECRET` required for the Unified Plane.

### Commands

**Sync Dynamic RunPod URL to Vercel:**
```bash
infisical run --env=production -- vercel env add VITE_API_URL production https://{NEW_POD_ID}-8000.proxy.runpod.net --force
```

## Examples
- "Run the Infisical handshake to connect to the vault"
- "Build a secret-safe Docker image without a local .env"
- "Start the local stack with runtime-injected secrets"
- "Deep prune my Docker system to free up space"
- "Push and deploy everything to production"

## Secret Management Policy (v2.5.3)

| Platform | Integration |
|---|---|
| **Vercel** | Infisical Vercel Integration auto-syncs `VITE_SUPABASE_URL`, `VITE_API_URL` |
| **RunPod** | Autoscaler uses `INFISICAL_TOKEN` to pull `MERCURY_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY` dynamically |
| **GitHub Actions** | Infisical secrets-action fetches Docker credentials from Infisical at runtime. Only `INFISICAL_CLIENT_ID` and `INFISICAL_CLIENT_SECRET` stored in GitHub. |

## Skill 5: Action-Vault Sync

Verifies Infisical secrets are ready for GitHub consumption.

### Commands

```bash
# Check secrets in prod environment
infisical export --env="prod" --format="dotenv"
echo "✅ Antigravity: Secrets verified in Infisical prod environment."
```

## Skill 6: Silent Deploy

Forces a fresh GitHub push that triggers the Infisical-injected workflow.

```bash
git add .
git commit -m "v2.5.3: Secret-Ops Migration"
git push origin main
echo "✅ Antigravity: Deployment triggered. Check GitHub Actions."
```
