---
name: docker-lean
description: Minimal, reproducible Docker builds for SimHPC GPU workloads (A40 optimized).
version: 2.7.1
license: MIT
compatibility: opencode
---

# Docker Lean Skill Set (v2.7.1)

Essential skills for keeping images small and your system clean.

## Version: 2.7.1

## 🔐 SECURITY RULES (MANDATORY - NO EXCEPTIONS)

### 🚨 NEVER include in Docker image:
- `.env` files (ANY variant)
- API keys, tokens, secrets
- SSH keys or credentials
- Database connection strings with passwords

### ✅ ALWAYS use Infisical for secrets in Docker:
```dockerfile
# In Dockerfile.unified - use runtime secrets only
RUN infisical secrets export --env=production --outputFormat=dotenv > /app/.env
# OR inject via docker run -e
```

### .dockerignore (CRITICAL):
```bash
.env
.env.local
.env.*
*.key
*.pem
*.secret
```

## SimHPC Image Topology (v2.7 Structure)

| Service           | Dockerfile              | Context |
| ----------------- | ---------------------- | ------- |
| simhpc-unified    | `docker/images/Dockerfile.unified` | root |
| simhpc-worker     | `docker/images/Dockerfile.worker` | root |
| simhpc-api        | `docker/images/Dockerfile.api` | root |
| simhpc-autoscaler | `docker/images/Dockerfile.autoscaler` | root |
| start.sh          | `docker/scripts/start.sh` | - |

**Rule:**
* Use `unified` for RunPod deployments (default)
* Use split services for scaling + isolation
* Always use root as build context: `docker build -f docker/images/Dockerfile.unified .`

## Base Image Strategy (GPU-Optimized)

**MANDATORY for A40 pods:**

```dockerfile
FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04
```

Avoid:
* `devel` images (too large)
* full Ubuntu images unless required

## Multi-Stage Build (Size Reduction)

```dockerfile
# Builder
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime
FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY . .

CMD ["python", "main.py"]
```

**Impact:**
* 40–70% smaller images
* removes build-time dependencies

## Layer Minimization

Combine commands:

```dockerfile
RUN apt-get update && apt-get install -y \
    build-essential \
 && rm -rf /var/lib/apt/lists/*
```

Python:

```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

## .dockerignore (CRITICAL)

```bash
.git
.gitignore
node_modules
__pycache__
*.pyc
.env
*.log
dist
build
```

**Impact:** prevents massive context uploads to Docker daemon.

## Build SOP (CI First)

### Primary (GitHub Actions)

```bash
git push origin main
```

Pipeline must:
1. Use `docker buildx`
2. Enable layer caching
3. Tag:
   * `:latest`
   * `:<git-sha>`

## Buildx + Cache (Required Upgrade)

```yaml
- uses: docker/setup-buildx-action@v3

- uses: docker/build-push-action@v5
  with:
    push: true
    tags: simhpcworker/simhpc-api:latest
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

## Manual Build (Fallback)

```bash
docker build --pull -f Dockerfile.unified -t simhpcworker/simhpc-unified:latest .
```

Debug mode:

```bash
docker build --no-cache -f Dockerfile.worker .
```

## Runtime (GPU Required)

```bash
docker run -d \
  --gpus all \
  --name simhpc-worker \
  simhpcworker/simhpc-worker:latest
```

## Image Inspection

```bash
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
```

Deep inspection:

```bash
docker history <image>
```

## Safe Cleanup

### Dev Cleanup

```bash
docker system prune -f
```

### Deep Cleanup (⚠ destructive)

```bash
docker system prune -a --volumes -f
docker builder prune -a -f
```

**Rule:** Never run deep prune on shared GPU nodes.

## Tagging Strategy (Production Safe)

Always deploy:

```bash
simhpcworker/simhpc-api:<git-sha>
```

Never rely on:

```bash
:latest
```

## Common Failure Modes

| Issue            | Cause            | Fix               |
| ---------------- | ---------------- | ----------------- |
| Huge images      | no .dockerignore | add ignore file   |
| Slow builds      | no cache         | enable buildx     |
| GPU not detected | wrong base image | use cuda runtime  |
| Pod crashes      | wrong CMD        | verify entrypoint |
| CI mismatch      | local vs CI env  | pin versions      |

## Examples

- "Apply multi-stage build to reduce my Docker image size"
- "Create a proper .dockerignore for SimHPC"
- "Prune my Docker system to free up space"
- "Deep prune to clear all Docker bloat"
- "Show me my largest Docker images"
- "Build with buildx and caching enabled"
- "Audit image layers for bloat"

## Docker History Audit (v2.6.8)

### Layer inspection
```bash
docker history simhpcworker/simhpc-unified:latest --format "table {{.CreatedBy}}\t{{.Size}}"
```

### Compare builds
```bash
docker history <old> > old.txt
docker history <new> > new.txt
diff old.txt new.txt
```

### CI size enforcement
```bash
SIZE=$(docker image inspect simhpcworker/simhpc-unified:latest --format='{{.Size}}')
MAX=$((5 * 1024 * 1024 * 1024))  # 5GB for GPU images
if [ "$SIZE" -gt "$MAX" ]; then
  echo "Image too large!"
  exit 1
fi
```

## start.sh Signal Handling (v2.6.8)

Always use trap for clean shutdowns:

```bash
trap "kill 0" SIGINT SIGTERM EXIT
```

This ensures clean termination of all background processes (API, worker, autoscaler) in RunPod.