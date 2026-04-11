---
name: deployment
description: Complete deployment pipeline for SimHPC - Vercel, GitHub, Docker Hub, Supabase, and RunPod.
version: 2.7.3
license: MIT
compatibility: opencode
---

# Deployment Skill Set (v2.7.3)

Complete deployment pipeline for SimHPC with production hardening.

## Version: 2.7.3

## 🔐 SECURITY RULES (MANDATORY - NO EXCEPTIONS)

### 🚨 NEVER commit to git:
- `.env` files (ANY variant: `.env.local`, `.env.production`, `.env.vercel`, etc.)
- API keys, tokens, secrets
- Database connection strings
- SSH keys or credentials
- OAuth client secrets
- Supabase service role keys
- RunPod API keys

### ✅ ALWAYS use Infisical:
```bash
# Pull secrets at runtime
infisical secrets export --env=production --outputFormat=dotenv > .env

# Run commands with secrets injected
infisical run --env=production -- your-command

# For Vercel deployment
infisical run --env=production -- vercel --prod --yes
```

### GitHub Actions secrets:
- Store secrets in GitHub Secrets ONLY
- Reference via `${{ secrets.SECRET_NAME }}`
- NEVER log secrets in workflow output

### Pre-push checklist:
```bash
# Before ANY commit, run:
grep -r "API_KEY\|SECRET\|TOKEN\|PASSWORD" --include="*.env*" .
# Should return NO matches in tracked files
```

## Docker Images

All images pushed to Docker Hub with SHA tagging (NOT latest):

| Image | Tag | Purpose |
| :--- | :--- | :--- |
| simhpcworker/simhpc-unified | `${{ github.sha }}` | Combined API + Worker + Autoscaler (Port 8080) |
| simhpcworker/simhpc-worker | `${{ github.sha }}` | GPU physics worker |
| simhpcworker/simhpc-api | `${{ github.sha }}` | FastAPI orchestrator |
| simhpcworker/simhpc-autoscaler | `${{ github.sha }}` | RunPod autoscaler |

**CRITICAL: Always use SHA tags, never deploy `latest` in production.**

## Pipeline Verification Gates (v2.7.2)

### Failure Modes & Fixes

| Stage | Failure Mode | Fix |
|-------|-------------|-----|
| Docker push | Silent fail | Use `set -e` + exit on error |
| podReset | Fire-and-forget | Parse GraphQL response, check for errors |
| Tagging | `latest` cache | Use SHA tags (`${{ github.sha }}`) |
| No digest enforcement | RunPod uses cached image | Deploy exact SHA, not tag |
| File path mismatch | worker.py not found | Use correct paths: `app/api/api:app`, `app/services/worker/worker.py` |

### Verified Docker Push (MANDATORY)

```bash
set -e

IMAGE=simhpcworker/simhpc-unified:${{ github.sha }}

docker build -f docker/images/Dockerfile.unified -t $IMAGE .
docker push $IMAGE

echo "IMAGE=$IMAGE" >> $GITHUB_ENV
```

### Verified podReset (MANDATORY)

```bash
RESPONSE=$(curl -s -X POST "https://api.runpod.io/graphql" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "x-apollo-operation-name: podReset" \
  -d "{\"query\": \"mutation { podReset(input: { podId: \\\"$RUNPOD_ID\\\" }) { id status } }\"}")

echo "RunPod response: $RESPONSE"

if [[ "$RESPONSE" == *"errors"* ]] || [[ "$RESPONSE" == *"error"* ]]; then
  echo "Deployment failed"
  exit 1
fi
```

## Job Execution Pipeline Audit (v2.7.1)

### CRITICAL: Double Execution Risk

**NEVER execute on both Redis AND RunPod simultaneously:**

```python
# WRONG - causes duplicate compute
enqueue_job(run_id, payload)
runpod_job_id = await client.run_job(payload)
```

```python
# CORRECT - exclusive execution mode
EXECUTION_MODE = os.getenv("EXECUTION_MODE", "runpod")

if EXECUTION_MODE == "local":
    enqueue_job(run_id, payload)
elif EXECUTION_MODE == "runpod":
    runpod_job_id = await client.run_job(payload)
```

### State Architecture (Source of Truth)

| System | Responsibility |
|--------|---------------|
| Supabase | Canonical state (source of truth) |
| Redis | Ephemeral cache only (status, not full job) |
| Worker | Compute only |

**NEVER store full job in Redis** - causes state drift:

```python
# WRONG
r_client.set(f"job:{sim_id}", json.dumps(job_data))

# CORRECT
r_client.set(f"job:{sim_id}:status", "queued", ex=300)
```

### Idempotency Enforcement

Propagate idempotency key to ALL layers:

```python
# Add to job payload
"idempotency_key": idempotency_key
```

Worker MUST check before execution:

```python
existing = supabase.table("simulations") \
    .select("id") \
    .eq("idempotency_key", key) \
    .execute()

if existing:
    skip execution
```

### Retry Fork Guard

Prevent forked retries:

```python
current_attempt = get_job_field(run_id, "attempt")

if attempt < current_attempt:
    return  # stale retry
```

### Lock Ownership (UUID-based)

```python
lock_value = str(uuid.uuid4())

acquired = r_client.set(lock_key, lock_value, nx=True, ex=300)

# On release:
if r_client.get(lock_key) == lock_value:
    r_client.delete(lock_key)
```

### Progress Update Ordering

```python
# Prevent UI regression (80% -> 40% -> 100%)
if new_progress < current_progress:
    return
```

### Recovery Worker Safety

Check RunPod status before recovery:

```python
status = await client.get_job_status(runpod_job_id)

if status in ["COMPLETED", "FAILED"]:
    skip recovery
```

## API-Only Deployment (v2.7.1)

**No SSH** - All deployments use GraphQL API:

### Secrets (v2.7.1) - Only CRITICAL vars

| Secret | Purpose | Status |
|--------|---------|--------|
| `RUNPOD_API_KEY` | GraphQL API key | CRITICAL |
| `RUNPOD_ID` | Pod identifier | CRITICAL |
| `DOCKER_LOGIN` | Docker Hub username | CRITICAL |
| `DOCKER_PW_TOKEN` | Docker Hub PAT | CRITICAL |

**Delete if present:**
- `RUNPOD_SSH_KEY` - Not needed
- `RUNPOD_SSH` - Not needed
- `RUNPOD_TCP_PORT_22` - Not needed
- `RUNPOD_USERNAME` - Not needed

## GitHub Actions Workflow (deploy.yml)

### PodReset vs PodRestart

| Action | Effect | Use Case |
|--------|--------|----------|
| `podRestart` | Reboots container, uses cached image | Quick debug |
| `podReset` | Wipes container, pulls fresh image | **CI/CD deployments (REQUIRED)** |

### Login to Docker Hub

```yaml
- name: Login to Docker Hub
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKER_LOGIN }}
    password: ${{ secrets.DOCKER_PW_TOKEN }}
```

### Safe Workflow (v2.7.1)

```yaml
name: deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_LOGIN }}
          password: ${{ secrets.DOCKER_PW_TOKEN }}

      - name: Build & Push Image (SHA tag)
        run: |
          set -e

          IMAGE=simhpcworker/simhpc-unified:${{ github.sha }}

          docker build -f Dockerfile.unified -t $IMAGE .
          docker push $IMAGE

          echo "IMAGE=$IMAGE" >> $GITHUB_ENV

      - name: Deploy to RunPod (podReset)
        run: |
          set -e

          RESPONSE=$(curl -s -X POST "https://api.runpod.io/graphql" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $RUNPOD_API_KEY" \
            -d "{\"query\": \"mutation { podReset(input: { podId: \\\"$RUNPOD_ID\\\" }) { id status } }\"}")

          echo "$RESPONSE"

          if [[ "$RESPONSE" == *"errors"* ]]; then
            echo "Deployment failed"
            exit 1
          fi

      - name: Post-deploy wait
        run: sleep 20
```

## Deployment Flow

```
┌─────────────────┐
│  Push to GitHub │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Build Image   │
│  (Docker)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Push to DH    │ ──→ SHA tag (${{ github.sha }})
│  (Docker Hub)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Verify Push    │ ──→ set -e + check exit code
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Deploy RunPod  │ ──→ podReset + GraphQL error check
│  (podReset)     │
└─────────────────┘
```

## Dockerfile Paths (v2.7 Structure)

### New Structure: `/docker` folder

| Image | Dockerfile | Context |
|-------|------------|---------|
| simhpc-unified | `docker/images/Dockerfile.unified` | root (build context) |
| simhpc-worker | `docker/images/Dockerfile.worker` | root |
| simhpc-api | `docker/images/Dockerfile.api` | root |
| simhpc-autoscaler | `docker/images/Dockerfile.autoscaler` | root |
| start.sh | `docker/scripts/start.sh` | - |

### Build Command (v2.7)

```bash
docker build -f docker/images/Dockerfile.unified -t simhpcworker/simhpc-unified:${{ github.sha }} .
```

**CRITICAL:** Always use root as build context, not `/docker`.

## Docker History SOP (v2.7)

### Layer inspection

```bash
docker history simhpcworker/simhpc-unified:latest --format "table {{.CreatedBy}}\t{{.Size}}"
```

### Full metadata

```bash
docker inspect simhpcworker/simhpc-unified:latest
```

### CI size budget enforcement

```bash
SIZE=$(docker image inspect simhpcworker/simhpc-unified:latest --format='{{.Size}}')
MAX=$((5 * 1024 * 1024 * 1024))  # 5GB for GPU images
if [ "$SIZE" -gt "$MAX" ]; then
  echo "Image too large!"
  exit 1
fi
```

## Common Failure Modes

| Issue | Cause | Fix |
|-------|-------|-----|
| Pod not updating | Using `latest` tag | Use SHA tag |
| podReset fails silently | No error parsing | Check for `"errors"` in response |
| Docker push fails | No exit on error | Use `set -e` |
| Duplicate jobs | Dual execution (Redis + RunPod) | Set EXECUTION_MODE |
| State drift | Full jobs in Redis | Use status-only in Redis |
| Race conditions | Weak locking | UUID-based lock with ownership |

## Examples

- "Build and push the unified image to Docker Hub with SHA tag"
- "Deploy a new GPU pod to RunPod with verification"
- "Verify job execution pipeline has no double execution"
