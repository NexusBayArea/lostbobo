---
name: docker-lean
description: Keep Docker images small and system clean for high-performance GPU pods like SimHPC A40s.
version: 2.6.6
license: MIT
 compatibility: opencode
---

# Docker Lean Skill Set

Essential skills for keeping images small and your system clean.

## Version: 2.6.6

## SimHPC Dockerfile Paths (v2.6.6)

| Image | Dockerfile | Context |
|-------|------------|---------|
| simhpc-unified | `Dockerfile.unified` | Root (combined API + Worker + Autoscaler) |
| simhpc-worker | `Dockerfile.worker` | Root |
| simhpc-api | `Dockerfile.api` | Root |
| simhpc-autoscaler | `Dockerfile.autoscaler` | Root |

## Build & Push SOP (via GitHub Actions)

**Preferred method** - Push to main triggers CI build + push:

```bash
git push origin main
```

GitHub Actions will:
1. Login to Docker Hub
2. Build all images
3. Push with `:latest` and `:<sha>` tags

### Manual Build (if CI fails)

```bash
# Unified (single pod - v2.6.6 default)
docker build -f Dockerfile.unified -t simhpcworker/simhpc-unified:latest .

# Individual services
docker build -f Dockerfile.worker -t simhpcworker/simhpc-worker:latest .
docker build -f Dockerfile.api -t simhpcworker/simhpc-api:latest .
docker build -f Dockerfile.autoscaler -t simhpcworker/simhpc-autoscaler:latest .

# Push to Docker Hub
docker push simhpcworker/simhpc-unified:latest
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

## Prune Commands

### Quick Prune
```bash
docker system prune
```

### Deep Prune
```bash
docker system prune -a --volumes -f
docker builder prune -a -f
```

## Image Size Audit
```bash
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
```

## Examples

- "Apply multi-stage build to reduce my Docker image size"
- "Create a proper .dockerignore for SimHPC"
- "Prune my Docker system to free up space"
- "Deep prune to clear all Docker bloat"
- "Show me my largest Docker images"
