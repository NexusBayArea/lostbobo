---
name: docker-lean
description: Keep Docker images small and system clean for high-performance GPU pods like SimHPC A40s.
version: 2.6.5
license: MIT
 compatibility: opencode
---

# Docker Lean Skill Set

Essential skills for keeping images small and your system clean.

## Version: 2.6.5

## SimHPC Dockerfile Paths (v2.6.5)

| Image | Dockerfile | Context |
|-------|------------|---------|
| simhpc-unified | `Dockerfile.unified` | Root (combined API + Worker + Autoscaler) |
| simhpc-worker | `Dockerfile.worker` | Root |
| simhpc-api | `Dockerfile.api` | Root |
| simhpc-autoscaler | `Dockerfile.autoscaler` | Root |

### Build Commands

```bash
# Unified (single pod - v2.6.5 default)
docker build -f Dockerfile.unified -t simhpcworker/simhpc-unified:latest .

# Individual services
docker build -f Dockerfile.worker -t simhpcworker/simhpc-worker:latest .
docker build -f Dockerfile.api -t simhpcworker/simhpc-api:latest .
docker build -f Dockerfile.autoscaler -t simhpcworker/simhpc-autoscaler:latest .
```

## GitHub Actions Build Matrix

```yaml
jobs:
  build:
    strategy:
      matrix:
        service: [worker, api, autoscaler]
```

### Dynamic Dockerfile Mapping

```bash
if [ "${{ matrix.service }}" = "worker" ]; then
  echo "file=Dockerfile.worker" >> $GITHUB_OUTPUT
elif [ "${{ matrix.service }}" = "api" ]; then
  echo "file=Dockerfile.api" >> $GITHUB_OUTPUT
elif [ "${{ matrix.service }}" = "autoscaler" ]; then
  echo "file=Dockerfile.autoscaler" >> $GITHUB_OUTPUT
fi
```

## Skill 1: Multi-Stage Build

Use a heavy build image with all tools to compile your app, then copy only the finished binaries to a tiny runtime image.

### Dockerfile Template

```dockerfile
# Stage 1: Build (Heavy)
FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime (Tiny)
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "api.py"]
```

### Build Command

```bash
docker build -t myapp:latest .
```

## Skill 2: Clean Up in Same RUN Layer

Docker saves a snapshot of every RUN command. Install and cleanup in the same layer.

### Commands

**Bad:**
```dockerfile
RUN apt-get update
RUN apt-get install -y git
```

**Good:**
```dockerfile
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
```

## Skill 3: .dockerignore

Prevent large or sensitive files from being copied into your image.

### Commands

```
.git/
__pycache__/
*.pdf
.env
.ipynb_checkpoints/
```

## Skill 4: Quick Prune

Remove all stopped containers, unused networks, and dangling images.

### Commands

```bash
docker system prune
```

## Skill 5: Deep Prune

Clear everything to prevent Docker bloat.

### Commands

```bash
docker system prune -a --volumes -f
docker builder prune -a -f
```

## Skill 6: Image Size Audit

Check the size of your Docker images.

### Commands

```bash
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
```

## Examples

- "Apply multi-stage build to reduce my Docker image size"
- "Create a proper .dockerignore for SimHPC"
- "Prune my Docker system to free up space"
- "Deep prune to clear all Docker bloat"
- "Show me my largest Docker images"
