---
name: runpod-push
description: Build, push, and deploy SimHPC worker to RunPod GPU instances with Infisical secret management.
version: 2.5.5
license: MIT
compatibility: opencode
---

# RunPod Push Skill Set

Build, push, and deploy SimHPC unified stack to RunPod GPU instances.

## Version: 2.5.5

## Unified Deployment

Deploy API, Worker, and Autoscaler in a single pod for maximum performance.

### Dockerfile.unified

```dockerfile
FROM nvidia/cuda:12.8.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONPATH=/app
WORKDIR /app

RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    python3-pip python3-dev git curl bash gcc && \
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

EXPOSE 8000
CMD ["./start.sh"]
```

### start.sh (Unified Orchestrator)

```bash
#!/bin/bash

echo "Starting SimHPC v2.5.4 Unified..."

cd /app
export PYTHONPATH=/app

echo "Starting FastAPI Gateway (Port 8000)..."
python3 -m uvicorn api:app --host 0.0.0.0 --port 8000 --forwarded-allow-ips='*' &

echo "Starting Physics Worker..."
python3 -u worker.py &

echo "Starting Autoscaler..."
python3 -u autoscaler.py &

wait
```

## Phase 4: Dynamic Pod Synchronization

When a new Pod is provisioned, capture and inject values into the pipeline:

1. **`RUNPOD_POD_ID`**: The unique identifier (e.g., `q8sk0ehjvmevy6`)
2. **`RUNPOD_HTTPS_PROXY`**: `https://{POD_ID}-8000.proxy.runpod.net`
3. **`RUNPOD_SSH_CMD`**: `ssh root@{POD_IP} -p {PORT}`

### sync-pod.sh Script

Add this script to `scripts/sync-pod.sh` to automate Infisical and Vercel updates:

```bash
#!/bin/bash
# Usage: ./scripts/sync-pod.sh <POD_ID>

POD_ID=$1
HTTPS_URL="https://${POD_ID}-8000.proxy.runpod.net"

if [ -z "$POD_ID" ]; then
    echo "Error: No Pod ID provided."
    exit 1
fi

echo "Updating Infisical with new Pod Metadata..."
infisical secrets set RUNPOD_POD_ID=$POD_ID --env=production
infisical secrets set VITE_API_URL=$HTTPS_URL --env=production

echo "Triggering Vercel Frontend Update..."
infisical run --env=production -- vercel env add VITE_API_URL production $HTTPS_URL --force
infisical run --env=production -- vercel --prod --yes

echo "Sync Complete. Frontend is now pointing to $HTTPS_URL"
```

## Build & Deploy Commands

```bash
# Build
docker build -f Dockerfile.unified -t simhpcworker/simhpc-unified:latest .

# Push
docker push simhpcworker/simhpc-unified:latest

# Deploy (Python)
python scripts/deploy_unified.py
```

## Complete Deploy Script (v2.5.5)

Use this script to build, deploy, and sync the entire stack:

```bash
#!/bin/bash

echo "[1/5] Building & Pushing Unified Docker Image..."
docker build -f Dockerfile.unified -t simhpcworker/simhpc-unified:latest .
docker push simhpcworker/simhpc-unified:latest

echo "[2/5] Provisioning New RunPod Instance..."
NEW_POD_ID=$(python3 scripts/deploy_unified.py | grep -oP '(?<=pod_id: )[a-z0-9]+')

echo "[3/5] Syncing Metadata to Infisical & Vercel..."
./scripts/sync-pod.sh $NEW_POD_ID

echo "[4/5] Updating GitHub Repository..."
git add .
git commit -m "deploy: update pod to $NEW_POD_ID"
git push origin main

echo "[5/5] Fleet Synchronized."
```

## Current Deployment (v2.5.5)

| Service | Pod Name | Pod ID | GPU | HTTP Proxy |
|---|---|---|---|---|
| Unified | SimHPC-Unified-v2.5.5 | q41n3g4zwr84wt | NVIDIA A40 | https://q41n3g4zwr84wt-8000.proxy.runpod.net |

**Vercel**: https://frontend-chi-plum-13.vercel.app

## Infisical Integration

Use Infisical for secret management instead of hardcoded env vars.

## Examples

- "Build and push the unified image to Docker Hub"
- "Deploy a new GPU pod to RunPod"
- "Sync new pod metadata to Infisical and Vercel"
- "Sync secrets and deploy with Infisical"
