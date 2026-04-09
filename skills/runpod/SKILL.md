---
name: runpod-push
description: Build, push, and deploy SimHPC worker to RunPod GPU instances with Infisical secret management.
version: 2.6.4
license: MIT
compatibility: opencode
---

# RunPod Push Skill Set

Build, push, and deploy SimHPC unified stack to RunPod GPU instances.

## Version: 2.6.4 (Port 8888 + API Deployment)

## Vault-First Protocol

**Golden Rule:** Never put secrets in files tracked by Git. Use `os.getenv()` or `infisical run --` to inject secrets at runtime.

### Required Infisical Keys

| Key | Purpose |
|-----|---------|
| `PORT` | Set to `8888` for RunPod compatibility |
| `RUNPOD_API_KEY` | GraphQL API for pod lifecycle |
| `RUNPOD_ID` | Pod identifier for restart |
| `VITE_API_URL` | Dynamic proxy URL (`https://{ID}-8888.proxy.runpod.net`) |
| `ALLOWED_ORIGINS` | CORS origins |

### RunPod Secrets (v2.6.4) - API Only, No SSH

| Secret | Value |
|--------|-------|
| `RUNPOD_API_KEY` | GraphQL API key |
| `RUNPOD_ID` | Pod ID |

## Unified Deployment

The stack is now configured to use **Port 8888**, as it is the most reliable "open" port on standard RunPod templates.

### Dockerfile.unified

```dockerfile
FROM nvidia/cuda:12.8.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONPATH=/app
WORKDIR /app

RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    python3-pip python3-dev git curl bash gcc psmisc && \
    curl -1sLf 'https://dl.cloudsmith.io/public/infisical/infisical-cli/setup.deb.sh' | bash && \
    apt-get install -y infisical && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --upgrade pip setuptools>=78.1.1 wheel>=0.38.1

COPY services/worker/requirements.txt ./req-worker.txt
COPY services/worker/requirements-autoscaler.txt ./req-auto.txt
RUN pip3 install --no-cache-dir -r req-worker.txt && \
    pip3 install --no-cache-dir -r req-auto.txt

COPY services/api/api.py .
COPY services/api/auth_utils.py .
COPY services/api/demo_access.py .
COPY services/api/job_queue.py .
COPY services/api/app/ ./app/

COPY services/worker/worker.py .
COPY services/worker/runpod_api.py .
COPY services/worker/autoscaler.py .

COPY services/worker/start.sh .

RUN useradd -m simuser && \
    chown -R simuser:simuser /app && \
    chmod +x start.sh

USER simuser

EXPOSE 8888
CMD ["./start.sh"]
```

### start.sh (Unified Orchestrator)

```bash
#!/bin/bash
echo "Starting SimHPC v2.6.4 Unified..."

# Ensure Port 8888 is free (kills default Jupyter Lab)
fuser -k 8888/tcp || true

cd /app
export PYTHONPATH=/app

echo "Starting FastAPI Gateway (Port 8888)..."
python3 -m uvicorn api:app --host 0.0.0.0 --port 8888 --forwarded-allow-ips='*' &

echo "Starting Physics Worker..."
python3 -u worker.py &

echo "Starting Autoscaler..."
python3 -u autoscaler.py &

wait
```

## Deploy Commands

```bash
# Push code to trigger GitHub Actions
git push origin main

# The workflow will:
# 1. Login to Docker Hub (using native synced secrets)
# 2. Build & push simhpcworker/simhpc-unified:latest
# 3. Deploy to RunPod via GraphQL API (podRestart)
```

### sync-pod.sh

```bash
#!/bin/bash
POD_ID=$1
HTTPS_URL="https://${POD_ID}-8888.proxy.runpod.net"

infisical secrets set RUNPOD_ID=$POD_ID --env=production
infisical secrets set VITE_API_URL=$HTTPS_URL --env=production
infisical run --env=production -- vercel env add VITE_API_URL production $HTTPS_URL --force
```

## Current Deployment (v2.6.4)

| Service | HTTP Proxy (8888) |
|---------|-------------------|
| Unified | https://{POD_ID}-8888.proxy.runpod.net |

**Docker Image**: simhpcworker/simhpc-unified:latest (v2.6.4)

**Vercel**: https://simhpc.com

## Manual Pod Restart (GraphQL API)

```bash
# Get current pod ID from Infisical
POD_ID=$(infisical secrets get RUNPOD_ID --env=production --plain)

# Restart via GraphQL API (no SSH needed)
curl -s -X POST "https://api.runpod.io/graphql" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -d "{\"query\": \"mutation { podRestart(podId: \\\"$POD_ID\\\") { id status } }\"}"
```

## Config Sync (Drift Detection)

Workers load config from Supabase with hash verification:

```python
# services/worker/config_loader.py
from supabase import create_client

supabase = create_client(os.getenv("SB_URL"), os.getenv("SB_SERVICE_ROLE_KEY"))

def load_config(env="prod"):
    return supabase.table("config_versions").select("config, hash").eq("env", env).order("created_at", ascending=False).limit(1).single().execute()

# Drift detection - worker auto-restarts if config changes
```

### Supabase Tables Required

```sql
create table config_versions (
  id uuid primary key default gen_random_uuid(),
  env text not null,
  config jsonb not null,
  hash text not null,
  created_at timestamptz default now()
);
```

## Examples

- "Build and push the unified image to Docker Hub"
- "Deploy a new GPU pod to RunPod"
- "Sync new pod metadata to Infisical and Vercel"