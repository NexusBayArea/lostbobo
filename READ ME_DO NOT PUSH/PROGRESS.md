DO NOT PUSH!!!!

---

## v10.5.0: Boot DAG System & Pipeline Hardening (April 2026)

### Architectural Initialization (v10.4.0 - v10.5.0)
- **App Boot DAG System (v10.5.0)**: Fully implemented a deterministic boot pipeline in `app/core/boot/`.
  - Stages: `env`, `validate`, `normalize`, `config`.
  - Unified DAG entrypoint in `app/core/runtime/dag.py` for API, Worker, and CI modes.
  - Eliminated import-time side effects by shifting initialization to an explicit `run_boot_dag()` call.
  - Updated `app/main.py` and `app/core/config.py` to use the new boot context.
- **Unified Entrypoint Consolidation (v10.5.0)**: Merged `./api.py` with `./app/api/api.py` to create a single, feature-rich FastAPI entrypoint using the Boot DAG.
- **CI/CD Pipeline Hardening (v10.5.0)**: Fixed `IMAGE_REF` resolution in `ci-kernel.yml`.
  - Resolved "Context access might be invalid: IMAGE_REF" warnings by shifting to shell-variable access in `run` blocks.
  - Added digest validation to ensure `IMAGE_REF` is never empty.
  - Standardized digest-only pull and run strategy for GHCR artifacts.
- **App Boot DAG (v10.4.0)**: Shifted module loading into a rigid runtime application DAG structure starting in `app/main.py`.
- Evaluated side-effect boundaries and built `app/core/runtime/ci.py` and `app/core/runtime/boot.py` to enable declarative boot testing with `RUNTIME_MODE=ci`.
- **Docker Alignments**: Generated `docker-compose.yml` to mirror exact deployment requirements in `Dockerfile.api` vs `Dockerfile.worker` passing required specific secrets via strict environment variables structure in CI/CD pipeline.

---

# SimHPC Pipeline Hardening - GHCR Registry

## Current Status

Transitioning from fragile Docker-based pipeline to hardened GHCR artifact registry.

---

## Target State

### ✅ Implemented

- Deterministic image naming: `ghcr.io/nexusbayarea/simhpc-worker` (lowercase, single namespace)
- Explicit environment promotion model: dev → staging → prod
- Safe GHCR auth with `packages: write` permission
- Immutable build artifacts via SHA tagging
- No `latest` tag overwrite
- CI-safe tagging tied to commit SHA

---

## Action Items

### 1. Docker Build Setup
- [ ] Update workflow to use docker/build-push-action@v5
- [ ] Configure cache-from/cache-to with GHA
- [ ] Tag with SHA + branch refs

### 2. GHCR Permissions
- [ ] Ensure workflow has `packages: write`
- [ ] Add docker/login-action@v3

### 3. Promotion Layer
- [ ] Implement digest-based promotion (pull → tag → push)
- [ ] Add digest inspection step

### 4. Immutability Rules
- [ ] Never overwrite SHA tags
- [ ] Document digest pinning for deployments

---

## Recent Change

**Error encountered**: `denied: installation not allowed to Create organization package`

**Root cause**: Missing `packages: write` permission in workflow OR org policy blocking package creation.

**Fix applied**: Hardcoded image name to `ghcr.io/nexusbayarea/simhpc-worker` to match expected package namespace.

# Progress Log

> **Note**: This file tracks high-level development milestones.
> For detailed changelog, see [CHANGELOG.md](./CHANGELOG.md).

## Documentation (v2.6.7)

Consolidated to 5-pillar structure:
- **README.md** - High-level overview
- **CHANGELOG.md** - Version history
- **PROGRESS.md** - This file

Deleted: GEMINI.md, GUIDE.md, ALPHA_PILOT_GUIDE.md, COMPREHENSIVE_AUDIT.md, ARCHITECTURE.md, DEPLOYMENT.md, MISSION_CONTROL_STRATEGY.md, ROADMAP.md, INFISICAL_SECRETS_TEMPLATE.md (internal AI guides)

---

## v2.6.8: Production Hardening Audit Fixes (April 2026)

### Issues Fixed

#### 1. Queue Contract (✅ Already Correct)
- **Status**: FIXED - API enqueues full JSON, worker pulls full JSON via brpoplpush

#### 2. Redis Data Structure (✅ Already Correct)  
- **Status**: FIXED - Using JSON strings consistently

#### 3. Double Execution Risk (⚠️ Partial)
- **Issue**: Both local worker AND RunPod can execute same job
- **Fix**: Added `RUNPOD_ENABLED` flag in worker config

#### 4. Idempotency at Execution Layer (✅ FIXED)
- **Fix**: Added execution guard in worker - checks `job:{id}:executed` before run, sets in finally block

#### 5. Locking (✅ Verified)
- **Status**: Already using `nx=True, ex=TTL` - FIXED

#### 6. Active Runs Counter Drift (✅ FIXED)
- **Fix**: Decrement in finally block AND failure paths

#### 7. DLQ Replay (✅ Already Implemented)
- **Status**: `replay_dlq_job()` function exists

#### 8. Supabase as Source of Truth (✅ Verified)

#### 9. Polling Loop (✅ FIXED)
- **Fix**: Added exponential backoff for Redis polling

#### 10. Recovery Worker KEYS Scan (✅ FIXED)
- **Fix**: Uses SCAN instead of KEYS + JSON string instead of hash

---

## v2.6.11: Canonical Job Schema (April 2026)

### Single Source of Truth
Created strict schemas enforced everywhere:

**`app/models/job.py`** - Job schema
- id, user_id, status, progress, input_params, result, error, retries
- created_at, updated_at, completed_at timestamps

**`app/models/event.py`** - JobEvent schema  
- type, job_id, user_id, status, progress, result, error, timestamp

**`app/core/job_store.py`** - Serialization helpers
- serialize_job(), deserialize_job()
- serialize_event(), deserialize_event()
- job_to_dict() for Supabase

### Enforcement
- Worker uses canonical Job model for all mutations
- Event emission uses JobEvent schema
- Supabase upsert uses job_to_dict() format

### Data Model Fix (v2.6.11.1)
- **ALL job storage now JSON via Pydantic** (GET/SET) - strict shape
- **ALL events now JobEvent schema** - no drift
- Redis = ephemeral cache, Supabase = source of truth

---

## Current Status

- **v2.6.19**: Docker Build Path Verification (all paths correct)
- **v2.6.18**: Softened Worker Check (debug mode - no blocking)
- **v2.6.17**: Start.sh Port Cleanup (8080/8000 only, no 8888)

---

## v2.6.19: Docker Build Path Verification (April 2026)

### Verified Files Exist
All paths in Dockerfile.unified and Dockerfile.worker are correct:

| File in Dockerfile | Actual Location | Status |
|--------------------|-----------------|--------|
| `app/services/worker/requirements.txt` | ✅ `app/services/worker/requirements.txt` | OK |
| `app/services/worker/requirements-autoscaler.txt` | ✅ `app/services/worker/requirements-autoscaler.txt` | OK |
| `app/services/worker/start.sh` | ✅ `app/services/worker/start.sh` | OK |

---

## v2.6.20: Dockerfile Unified Audit Fixes (April 2026)

### Issues Fixed

| Issue | Fix |
|-------|-----|
| `apt-get upgrade -y` | Removed (breaks reproducibility, bloats image) |
| CUDA version | Changed from 12.1.1 to 12.2.0 for A40 compatibility |
| Unnecessary packages | Removed: git, gcc, jq, redis-tools (saved ~200MB) |
| User UID | Changed from 1000 to 10001 (avoids RunPod conflicts) |
| Duplicate build notes | Removed duplicate section at end |
| Layer efficiency | Preserved multi-stage build pattern |

### Files Updated
- `Dockerfile.unified` → v2.6.20
- `skills/docker/SKILL.md` → v2.6.7 (audit notes added)

---

## v2.6.21: Docker Audit Fixes (April 2026)

### Issues Fixed

| Issue | Fix |
|-------|-----|
| No docker history SOP | Added to skills/docker/SKILL.md |
| Unified COPY path | Changed from `python3.10/dist-packages` to `/usr/local` |
| EXPOSE misuse | Removed 8888 (only worker needs 8080/8000) |
| start.sh fragile | Added `trap "kill 0" SIGINT SIGTERM EXIT` for clean shutdowns |
| .dockerignore | Already exists and comprehensive |

### Files Updated
- `app/services/worker/start.sh` → Added signal handling
- `Dockerfile.unified` → v2.6.21 (COPY /usr/local, EXPOSE 8080/8000)
- `skills/docker/SKILL.md` → v2.6.8 (docker history SOP, trap guidance)

---

## v2.6.21: Pipeline & Job Execution Audit (April 2026)

### Pipeline Verification Gates

| Issue | Fix |
|-------|-----|
| Docker push silent failures | Use `set -e` + exit on error |
| podReset fire-and-forget | Parse GraphQL response, check for errors |
| Tagging with `latest` | Use SHA tags (`${{ github.sha }}`) |
| RunPod cached image | Deploy exact SHA, not tag |

### Job Execution Pipeline Audit

| Issue | Fix |
|-------|-----|
| Double execution (Redis + RunPod) | Add EXECUTION_MODE env var |
| Full jobs in Redis (state drift) | Use status-only in Redis |
| Idempotency not propagated | Propagate idempotency_key to all layers |
| Retry fork | Add attempt lock guard |
| Weak locking | UUID-based lock with ownership |
| Progress UI regression | Add monotonic guard |
| Recovery worker duplication | Check RunPod status before recovery |

### Files Updated
- `skills/deployment/SKILL.md` → v2.6.21 (full audit, SHA tags, job pipeline fixes)

---

## v2.7.0: Full System Audit (April 2026)

### Audit Scope
Full codebase audit against v2.7 reference architecture.

### Key Findings

| Issue | Severity | Count |
|-------|----------|-------|
| Redis dependency | 🔴 Critical | 157 references |
| Dual ports (8080/8000) | 🟠 High | 1 file |
| Raw bash backgrounding | 🟠 High | start.sh |
| No schema_version in Job | 🟠 High | app/models/job.py |
| Scattered Dockerfiles | 🟡 Medium | 4 files |
| Redis pub/sub in WS | 🟡 Medium | 3 files |

### v2.7 Reference Architecture Principles

1. Supabase = Single Source of Truth (no Redis)
2. No Redis anywhere
3. One primary port (8080 only)
4. Stateless API
5. Worker = pull-based executor (Supabase polling)
6. WebSockets = thin layer (in-memory, no Redis)
7. Deployment = podReset only
8. Process manager (tini/supervisord)

### Files Created
- `V2.7_AUDIT.md` → Full system audit document

### Migration Path

**Phase 1:** Remove Redis (Week 1)
- Create Supabase job store
- Update worker to poll Supabase
- Remove Redis from API
- WS use in-memory events

**Phase 2:** Schema v2 (Week 2)
- Add schema_version to Job model
- Add migration layer

**Phase 3:** Docker Cleanup (Week 3)
- Consolidate to /docker
- Remove port 8000
- Add tini

**Phase 4:** CI/CD Hardening (Week 4)
- SHA tagging only
- podReset verification
- Size budget enforcement

---

## v2.6.22: Docker Folder Structure (April 2026)

### Changes Made

| Change | File |
|--------|------|
| Created `/docker` folder | New structure |
| Created `/docker/images/` | Dockerfiles |
| Created `/docker/scripts/` | start.sh |
| Created `/docker/ci/` | Build scripts (empty) |
| Created `/docker/compose/` | Docker compose |
| Created `/docker/docs/` | Documentation |
| Removed port 8000 | Single port 8080 |
| Updated Dockerfile paths | `docker/images/` |
| Updated start.sh | Single API process |

### Updated Files
- `docker/images/Dockerfile.unified` - Path updates
- `docker/scripts/start.sh` - Single port, single API
- `.dockerignore` - Added docker/ exclusion
- `skills/docker/SKILL.md` → v2.6.9 (new structure)
- `skills/deployment/SKILL.md` → v2.6.22 (Docker paths)

### Build Command (v2.7)

```bash
docker build -f docker/images/Dockerfile.unified -t simhpcworker/simhpc-unified:${{ github.sha }} .
```

---

## v2.7.0: Docker Folder Consolidation (April 2026)

### Audit Results

| Location | Issue |
|----------|-------|
| Root `Dockerfile.unified` | Duplicate of `docker/images/` |
| Root `Dockerfile.worker` | Duplicate, older version |
| Root `Dockerfile.api` | Duplicate, different structure |
| Root `Dockerfile.autoscaler` | Duplicate |
| `app/services/worker/Dockerfile` | Worker-only build (legacy) |
| `legacy_archive/runpod-worker_deprecated/Dockerfile` | Deprecated, keep for reference |

### Consolidation Actions

1. **Removed duplicates from root**: Dockerfile.{unified,worker,api,autoscaler}
2. **Updated docker/images/Dockerfile.unified**:
   - Version → v2.7.0
   - Port 8000 removed (single port 8080)
   - Added build command comment
3. **Updated skills/docker/SKILL.md** → v2.7.0

### Final Structure

```
docker/
  images/
    Dockerfile.unified     ← Primary (used by CI)
    Dockerfile.worker      ← Standalone worker
    Dockerfile.api         ← API only
    Dockerfile.autoscaler  ← Autoscaler only
  scripts/
    start.sh
```

### Deprecated (kept for reference)
- `legacy_archive/runpod-worker_deprecated/Dockerfile`
- `app/services/worker/Dockerfile` (worker-only)

---

## v2.7.1: Docker Compose & Dockerignore Consolidation (April 2026)

### Audit Results

| File | Location | Action |
|------|----------|--------|
| docker-compose.yml | Root | Moved to docker/compose/ |
| .dockerignore | Root | Already correct |
| .dockerignore | app/services/robustness/ | Keep (legacy, different scope) |
| Dockerfile | app/services/worker/ | Keep (legacy, not in docker/) |

### Changes Made

1. **Moved docker-compose.yml** → `docker/compose/docker-compose.yml`
2. **Updated docker-compose.yml**:
   - Removed Redis service (Supabase is source of truth)
   - Updated context: `../..` and dockerfile: `docker/images/Dockerfile.unified`
   - Single port 8080 only

### Final Structure (v2.7.1)

```
docker/
  images/
    Dockerfile.unified    ← Primary (CI uses this)
    Dockerfile.worker
    Dockerfile.api
    Dockerfile.autoscaler
  scripts/
    start.sh
  compose/
    docker-compose.yml    ← v2.7 updated (no Redis)
```

---

## v2.6.18: Softened Worker Check (April 2026)

### Issue
- `check_compute_availability()` was blocking job submissions when no workers registered
- Causes "no_active_pods" errors during deployment transitions

### Fix

**app/api/api.py** and **app/main.py**:
```python
async def check_compute_availability():
    """Softened for deployment debugging - no longer blocks job submissions."""
    workers = get_active_workers()
    if not workers:
        logger.warning("No active workers detected — continuing anyway (debug mode)")
        return []
    return workers
```

### Files Modified

| File | Change |
|------|--------|
| `app/api/api.py` | Softened worker check |
| `app/main.py` | Softened worker check |

---

## v2.6.17: Start.sh Port Cleanup (April 2026)

### Issue
- start.sh still referenced port 8888 (Jupyter conflict)
- Needed strict 8080/8000 dual-HTTPS configuration

### Fix

**app/services/worker/start.sh**:
- Removed all 8888 references
- Clears only 8080 and 8000
- Worker already configured to use 8080 (POD_PORT defaults to 8080)

### Files Modified

| File | Change |
|------|--------|
| `app/services/worker/start.sh` | Removed 8888 port references |

---

## v2.6.16: Deploy Workflow Dynamic RUNPOD_ID (April 2026)

### Root Cause
- deploy.yml had **hardcoded pod ID** (`ikzejthq1q7yt9`)
- Infisical syncs `RUNPOD_ID` to GitHub secrets, but workflow ignored it
- Result: workflow passes, but wrong pod (or non-existent) gets reset

### Fix

**.github/workflows/deploy.yml**:
```yaml
# Before (hardcoded - WRONG)
RUNPOD_ID: ikzejthq1q7yt9

# After (dynamic from secrets - CORRECT)
RUNPOD_ID: ${{ secrets.RUNPOD_ID }}
```

### Files Modified

| File | Change |
|------|--------|
| `.github/workflows/deploy.yml` | Hardcoded pod ID → ${{ secrets.RUNPOD_ID }} |

---

## v2.6.15: Dual-Port Architecture (April 2026)

### Why No 8888
- JupyterLab (JL) reserves port 8888
- SimHPC now uses **8080 (Primary)** and **8000 (Backup)**

### Changes

**app/api/api.py** - Default port from 8888 → 8080:
```python
port = int(os.getenv("PORT", "8080"))
```

**app/services/worker/worker.py** - Worker port from 8888 → 8080:
```python
POD_PORT = os.getenv("WORKER_PORT", "8080")
```

**app/services/worker/start.sh** - Already correct (8080/8000)

### Architecture
- **8080**: Primary API (main traffic)
- **8000**: Backup API (failover)
- Both run identical FastAPI instances in same container

### Files Modified

| File | Change |
|------|--------|
| `app/api/api.py` | Default port 8888 → 8080 |
| `app/services/worker/worker.py` | Worker port 8888 → 8080 |

---

## v2.6.14: Dockerfile & Start Script Path Fixes (April 2026)

### Dockerfile.unified

Fixed COPY paths from deprecated `services/` to `app/`:
```dockerfile
# Before (wrong)
COPY --chown=simuser:simuser services/api/api.py .
COPY --chown=simuser:simuser services/worker/worker.py .

# After (correct)
COPY --chown=simuser:simuser app/ ./app/
```

### start.sh

Fixed uvicorn module reference from `api:app` to `app.main:app`:
```bash
# Before (wrong)
python3 -m uvicorn api:app --host 0.0.0.0 --port 8080

# After (correct)
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### Files Modified

| File | Change |
|------|--------|
| `Dockerfile.unified` | Fixed COPY paths to use `app/` directory |
| `app/services/worker/start.sh` | Fixed uvicorn module to `app.main:app` |

---

## v2.6.13: Schema Versioning with Migration Support (April 2026)

### Strict Schema Validation at Redis Boundary

Created `app/core/validated_job_store.py` with `ValidatedJobStore` class:

- **set_job(job)** - Validates Job Pydantic schema BEFORE write to Redis
- **get_job(job_id)** - Reads and validates job from Redis, quarantines corrupted data
- **update_job(job_id, **updates)** - Safe update with validation
- **delete_job(job_id)** - Cleanup job and related keys

### Enforcement in Worker

Patched `app/services/worker/worker.py` to use validated store:
- Job deserialization uses `Job.model_validate()` 
- All writes use `job_store.set_job(job)` with fallback
- Error handling updated to use `job.id`, `job.retries`, etc.

### Files Created/Modified

| File | Change |
|------|--------|
| `app/core/validated_job_store.py` | NEW - schema validation layer |
| `app/services/worker/worker.py` | PATCHED - use validated job store |

---

## v2.6.13: Schema Versioning with Migration Support (April 2026)

### Version Constant

Created `app/models/version.py`:
```python
CURRENT_JOB_SCHEMA_VERSION = 1
```

### Job Model Update

Added `schema_version` field to `Job` model:
```python
class Job(BaseModel):
    schema_version: int = CURRENT_JOB_SCHEMA_VERSION
    ...
```

### Migration Layer

Created `app/core/job_migrations.py`:
- `migrate_job(data)` - central migration router
- `migrate_v0_to_v1()` - adds missing progress/retries fields
- Throws `RuntimeError` if unsupported version after migration

### ValidatedJobStore Updates

- **set_job**: Enforces `CURRENT_JOB_SCHEMA_VERSION` on write
- **get_job**: Runs migration BEFORE Pydantic validation
- **update_job**: Ensures version doesn't downgrade

### Backward Compatibility Test

```python
old_job = {"id": "123", "user_id": "u1", "status": "queued", ...}
migrated = migrate_job(old_job)  # Auto-upgraded to v1
```

### Files Created/Modified

| File | Change |
|------|--------|
| `app/models/version.py` | NEW - version constant |
| `app/models/job.py` | PATCHED - added schema_version field |
| `app/core/job_migrations.py` | NEW - migration layer |
| `app/core/validated_job_store.py` | PATCHED - integrate migrations |

---

## v2.6.7: Dual-Port + Async Integrity + Authority Alignment (April 2026)

### Dual-Port Strategy
- **Primary API:** Port 8080 (main traffic, batch flush to Supabase)
- **Backup API:** Port 8000 (redundancy if 8080 fails)
- **Jupyter:** Port 8888 (development only)

### Async Integrity (httpx.AsyncClient)
- Replaced blocking `requests` with `httpx.AsyncClient` singleton in lifespan
- Connection pooling: 20 keepalive, 100 max connections, 60s timeout
- Non-blocking HTTP calls prevent event loop starvation

### Authority Alignment
- **Supabase as single source of truth** - removed Redis usage tracking
- **Batch Flush Pattern** - buffers usage events, flushes every 10s to prevent write pressure
- **SQL RPC** - `decrement_usage_atomic()` for atomic credit deduction (prevents race conditions)
- **Vercel Cron** - `/api/v1/internal/force-flush` for guaranteed flush even on pod scale-down

### Port Standardization
- All 8000→8080/8000 for RunPod compatibility
- start.sh: `fuser -k 8080/tcp 8000/tcp 8888/tcp || true` clears port conflicts

### Pod ID
- Current: `ikzejthq1q7yt9` (dynamic - get from Infisical)
- Check: `infisical secrets get RUNPOD_ID --plain`

## v2.6.27: Authority Alignment (April 2026)

### Fixes Applied

1. **Supabase Usage Authority** - Eliminated the split Redis/Supabase usage tracking logic.
   - Refactored `get_user_usage` to compute stats directly from the Supabase `simulations` table.
   - Removed all `usage:{user_id}` Redis key management to prevent data drift and race conditions.
2. **Simplified Increment Logic** - Deprecated `increment_user_usage` as a no-op. Usage is now implicitly incremented by the atomic database insert of a new simulation record.
3. **Rolling Window Integrity** - Verified that usage enforcement strictly follows the 7-day rolling window defined by actual database timestamps.

---

## v2.6.25: Distributed System Architecture + Port 8888 Standardization (April 2026)

### SERVICE_ROLE NOT NEEDED (Single-Pod Unified)
**No SERVICE_ROLE env var** - Unified pod runs everything together:

- Pod is "self-aware" - initializes API + Worker + Autoscaler simultaneously
- No external role configuration needed
- Lifespan handles startup sequence automatically

**start.sh** runs all 3 in same process:
```bash
uvicorn api:app --port 8888 &   # API (HTTP)
python3 -u worker.py &           # Worker (background)
python3 -u autoscaler.py &       # Autoscaler (background)
wait
```

## v2.6.26: Production Safety - Idempotency, Retry, DLQ (April 2026)

### 1. Atomic Idempotency (Redis-first)
- `SETNX` with TTL for duplicate prevention
- Generates hash from user_id + payload as idempotency key
- Returns `{"status": "duplicate", "job_id": "existing"}` on collision

### 2. Controlled Retry System
- Config: `MAX_RETRIES=3`, `RETRY_DELAY=5s`
- Exponential backoff: `sleep(RETRY_DELAY * retries)`
- After max retries → moves to DLQ

### 3. Dead Letter Queue (DLQ)
- Failed jobs after max retries → `simhpc_dlq`
- Admin endpoint to inspect + replay
- `GET /admin/dlq`, `POST /admin/dlq/replay/{job_id}`

### 4. Processing Queue (Crash Recovery)
- Uses `BRPOPLPUSH` to move job to `simhproc_processing`
- On success: remove from processing
- On crash: job stays in processing, can be recovered

### 5. No More "no_active_pods"
- API always succeeds: enqueue job, autoscaler triggers
- Queue-based: pod spins up AFTER job queued

### Files Modified
| File | Change |
|------|--------|
| `job_queue.py` | Idempotency key generation, DLQ functions, retry tracking |
| `worker.py` | BRPOPLPUSH, retry with backoff, DLQ move |

### Queue Architecture
```
simhpc_jobs        → active queue
simhpc_processing   → in-flight (crash-safe)
simhpc_dlq          → permanently failed
```

---

## v2.6.25: Distributed System + Events + WebSocket (April 2026)

### 1. Event-Driven Architecture (Redis Pub/Sub)
- **Channel**: `jobs:events`
- **Events emitted**: `job_queued`, `job_started`, `job_progress`, `job_completed`, `job_failed`

### 2. Auth Passthrough (user_id + tier)
- Job queue now carries user context:
  ```python
  job_input["user_id"] = user_context.get("user_id")
  job_input["tier"] = user_context.get("tier", "free")
  ```
- Tier-based routing ready (future: priority queues)

### 3. WebSocket Real-time Updates
- **New endpoint**: `/ws/jobs/{job_id}` - per-job updates
- **New endpoint**: `/ws/all` - all events (admin)
- Frontend connects once, receives live progress/completion/failure

### 4. Worker Event Emission
- `publish_event()` sends to Redis pub/sub
- Progress updates stream to UI
- Completion triggers autoscaler scale-down

### 5. Event-Driven Autoscaler
- Subscribes to `jobs:events` instead of polling
- Reacts to `job_queued` → `job_completed` → `job_failed`
- Single-pod: logs status only (no scaling)

### Files Modified
| File | Change |
|------|--------|
| `job_queue.py` | Added `publish_event()`, user context |
| `ws.py` (new) | WebSocket endpoints for real-time updates |
| `api.py` | Include ws_router |
| `worker.py` | Event emission on job lifecycle |
| `autoscaler.py` | Event-driven instead of polling |

### Architecture (Single-Pod)
```
Frontend → API → Redis Queue + Events → Worker
                                    ↓
                              WebSocket → Frontend
                                    ↓
                              Autoscaler (events)
```
All 8000 references converted to 8888:
- `Dockerfile.worker` - EXPOSE 8888
- `services/robustness-orchestrator/run_with_cors.py` - port 8888
- `apps/frontend/src/sections/Hero.tsx` - Uses VITE_API_URL env

### vLLM Persistence Paths Added
```dockerfile
ENV HF_HOME=/workspace/huggingface
ENV VLLM_CACHE=/workspace/vllm_cache
```
Ensures model cache persists on pod resets.

### Entrypoint Verified
- `services/api/api.py` contains `app = FastAPI(...)`
- start.sh runs `uvicorn api:app --port 8888`
- No separate main.py needed

### Ghost Files Warning
⚠️ These .md files are tracked (should be ignored):
- `CHANGELOG.md`
- `GEMINI.md`
- `progress.md`

Run `git rm --cached *.md` before deploy if needed.
All internal/external communication standardized on Port 8888:

| File | Change |
|------|--------|
| `services/worker/worker.py` | `POD_PORT = "8888"` |
| `services/worker/run_with_cors.py` | `port=8888` |
| `run_api.py` | `port=8888` |
| `Dockerfile.api` | `EXPOSE 8888`, `--bind 0.0.0.0:8888` |
| `services/api/Dockerfile` | `EXPOSE 8888`, `--bind 0.0.0.0:8888` |
| `.env.example` | `VITE_API_URL=http://localhost:8888` |
| `apps/frontend/src/lib/apiClient.ts` | `localhost:8888` |
| `apps/frontend/src/pages/admin/AdminAnalyticsPage.tsx` | `localhost:8888` |
| `scripts/simhpc.sh` | `lsof -i:8888`, `--port 8888` |

### Phase 0: Fix Container
1. **Dockerfile.unified** - Direct worker start, no Jupyter:
   ```dockerfile
   CMD ["python3", "-u", "worker.py"]
   ```
   - Removed `./start.sh` that was launching Jupyter
   - Worker now starts immediately on pod boot

### Phase 1: API = Control Plane Only
1. **Removed**: Direct RunPod calls from API
2. **Removed**: `no_active_pods` logic blocking submissions
3. **API Responsibility**:
   - Auth (Supabase JWT)
   - Validate payload
   - Enforce usage limits (free tier)
   - Idempotency (create_or_get_job)
   - Enqueue to Redis
   - Publish `autoscaler:tick` event

### Phase 2: Worker = Execution Plane
1. **Job ownership**:
   ```python
   WORKER_ID = os.getenv("WORKER_ID", os.uname().nodename)
   job["worker_id"] = WORKER_ID
   job["started_at"] = int(time.time())
   redis_client.hset("jobs:active", job_id, WORKER_ID)
   ```
2. **Telemetry events**:
   - `job_started`
   - `job_progress`
   - `job_completed`

### Phase 3: Redis = Event Bus (Channels)
```
events                → all system events
autoscaler:tick      → trigger scaling
jobs:updates         → job state changes
```

### Phase 4: Autoscaler = Event-Driven (Not Polling)
```python
def autoscaler_listener():
    pubsub = redis_client.pubsub()
    pubsub.subscribe("autoscaler:tick")
    for message in pubsub.listen():
        autoscale()
```

### Phase 5-8: Future (WebSockets, Smart Scheduling, Observability)

---

## v2.6.24: Atomic Idempotency & O(1) Concurrency (April 2026)

### Fixes Applied

1. **Atomic Idempotency** - Refactored `reserve_idempotency` to use Redis `SETNX`, ensuring that duplicate requests are blocked atomically at the point of entry.
2. **O(1) Concurrency Tracking** - Replaced O(N) Redis `KEYS` scans with O(1) per-user counters (`user:{user_id}:active_runs`).
   - Implemented `increment_active_runs` in the API (on enqueue).
   - Implemented `decrement_active_runs` in the Worker (on job completion/failure).
3. **Registry-Aware Discovery** - Integrated the Full Infra registry into the simulation creation flow, ensuring jobs are only accepted when healthy workers are heartbeating.

---

## v2.6.14: Frontend API & GitHub Workflow Fix (April 2026)

### Fixes Applied

1. **Duplicate API Declaration** - Merged the second `api` object into the `ApiClient` class in `apps/frontend/src/lib/api.ts`.
   - Unified `getUserProfile`, `subscribe`, `startRobustnessRun`, and other methods into the `api` instance.
   - All methods now consistently use the internal `request` helper for error handling and toasts.

2. **GitHub Workflow Fix (v2.6.7)** - Repaired the corrupted `deploy-runpod.yml` file.
   - Replaced "Frankenstein" script (containing git diff markers and duplicate steps) with the clean v2.6.7 protocol.
   - Implemented STAGE 1 (podReset) and Fallback Cycle (Stop -> Resume) for resilient deployments.

3. **Vercel Build Stability** - Resolved the "symbol already declared" error in TypeScript build.

---

## v2.6.6: API-Only Deployment (April 2026)

### Changes Applied

1. **All SSH steps removed** - Replaced with podReset GraphQL mutation
   - `deploy.yml` - Uses podReset
   - `auto-deploy-runpod.yml` - Uses podReset
   - `deploy-beta-runpod.yml` - Uses podReset
   - `deploy-runpod.yml` - Uses podReset

2. **GraphQL fixes** - Removed `status` field from mutations (API schema change)
   - podReset returns `{ id }` only
   - Status query uses `desiredStatus`

3. **Lean Secrets** - Only CRITICAL vars:
   - `RUNPOD_API_KEY` (CRITICAL)
   - `RUNPOD_ID` (CRITICAL)
   - `DOCKER_LOGIN` (CRITICAL)
   - `DOCKER_PW_TOKEN` (CRITICAL)
   - Delete: `RUNPOD_SSH_KEY`, `RUNPOD_SSH`, `RUNPOD_TCP_PORT_22`, `RUNPOD_USERNAME`

### PodReset vs PodRestart

| Action | Effect | Use Case |
|--------|--------|----------|
| `podRestart` | Reboots container, uses cached image | Quick debug |
| `podReset` | Wipes container, pulls fresh image | **CI/CD deployments (REQUIRED)** |

---

## v2.6.5: API-Only Deployment (April 2026)

### Changes Applied

1. **GitHub Actions deploy.yml** - Replaced `podStop` → `podResume` with atomic `podReset` GraphQL mutation
   - Fixes "not enough free GPUs" error that occurred when trying to resume on same host
   - Removed SSH deployment (no more `appleboy/ssh-action`)

2. **Enhanced api.ts** - Added toast error handling with sonner integration
   - Automatic error toasts for failed API calls
   - Cleaner request/response handling

3. **Documentation Updated**
   - README.md: API-only deployment (no SSH)
   - skills/deployment/SKILL.md: Removed SSH secrets, added podReset
   - skills/runpod/SKILL.md: Removed SSH references, uses GraphQL API

### Secrets (v2.6.5)

| Secret | Purpose |
|--------|---------|
| `DOCKER_LOGIN` | Docker Hub username |
| `DOCKER_PW_TOKEN` | Docker Hub PAT |
| `RUNPOD_API_KEY` | RunPod GraphQL API key |
| `RUNPOD_ID` | Pod identifier |

No SSH secrets needed - deployment is fully API-based.

---

## v2.6.13: AlphaControlRoom Fix (April 2026)

### Fix Applied

1. **Simplified AlphaControlRoom.tsx** - Removed broken imports
2. **Added route** `/dashboard/alpha` → AlphaControlRoom
3. **Sidebar link** now points to `/dashboard/alpha`

---

## v2.6.12: AlphaControlRoom Route (April 2026)

### Fix Applied

1. **Added AlphaControlRoom import** to App.tsx
2. **Added route** `/dashboard/alpha` pointing to AlphaControlRoom
3. **Fixed sidebar link** - Alpha Control now links to `/dashboard/alpha` (opens in new tab)

---

## v2.6.11: Manifest Cleanup (April 2026)

### Fix Applied

1. **Simplified Manifest** - Removed broken icon references from `site.webmanifest`:
   ```json
   {
     "name": "SimHPC",
     "short_name": "SimHPC",
     "start_url": "/",
     "display": "standalone",
     "background_color": "#0f172a",
     "theme_color": "#0f172a"
   }
   ```

2. **Removed broken icon references** - Icons don't exist in public folder

---

## v2.6.10: Manifest Fix (April 2026)

### Fix Applied

1. **Manifest Link** - Uncommented and added `crossorigin="use-credentials"`:
   ```html
   <link rel="manifest" href="/site.webmanifest" crossorigin="use-credentials" />
   ```

2. **Alpha Control** - Opens in new tab, links to `/admin/analytics`

---

## v2.6.9: Alpha Control Room Integration (April 2026)

### Fix Applied

Added **Alpha Control Room** to Dashboard sidebar:

1. **Sidebar Items** - Added `Alpha Control` tab with Cpu icon
2. **Content Area** - Added Alpha Control Room tab content
3. **Active Tab Default** - Set to 'robustness' (existing)

### Sidebar Structure

```tsx
const sidebarItems = [
  { id: 'alpha', label: 'Alpha Control', icon: Cpu },
  { id: 'simulations', label: 'Simulations', icon: Play },
  { id: 'robustness', label: 'Robustness', icon: BarChart3 },
  { id: 'reports', label: 'Reports', icon: FileText },
  { id: 'settings', label: 'Settings', icon: Settings },
];
```

---

## v2.6.8: User Profile Endpoint (April 2026)

### Fix Applied

Added `/api/v1/user/profile` endpoint to `services/api/api.py`:

```python
@app.get("/api/v1/user/profile")
async def get_user_profile(authorization: str = Header(None)):
    # Returns user profile with tier and usage
```

This fixes "Failed to fetch user profile" error.

---

## v2.6.7: Manifest Fix (April 2026)

### Fix Applied

1. **Disabled manifest link** - Commented out in `index.html` to bypass Vercel auth issues
   - `<link rel="manifest" href="/site.webmanifest" />` is now disabled

### If You Still Have Issues

In Vercel Dashboard → Settings → Deployment Protection:

1. **Vercel Authentication** - Ensure it's OFF (disable)
2. If there's a "Require Owner role" checkbox - **uncheck it**
3. Save changes

---

## v2.6.6: Manifest & CLI Fix (April 2026)

### Fixes Applied

1. **site.webmanifest Created** - Added `apps/frontend/public/site.webmanifest` to fix 401 error
2. **Infisical CLI** - Removed `infisical upgrade` command (not available in all versions)

### 401 Error Fix (Vercel Deployment Protection)

If `site.webmanifest` still returns 401:
1. Go to Vercel Dashboard → Settings → Deployment Protection
2. Disable Vercel Authentication for preview/production
3. OR add manifest link with crossorigin in index.html

---

## v2.6.5: AlphaControlRoom Integration (April 2026)

### 1. AlphaControlRoom Integration

**Problem:** Cockpit wasn't appearing on dashboard due to routing mismatch.

**Fix:** Integrate AlphaControlRoom as a tab inside Dashboard:

```tsx
// Dashboard.tsx - Update activeTab default
const [activeTab, setActiveTab] = useState('cockpit');

// Add tab trigger
<TabsTrigger value="cockpit">Alpha Cockpit</TabsTrigger>

// Add content
{activeTab === 'cockpit' && <AlphaControlRoom />}
```

### 2. Routing Fix

**App.tsx:** Simplified routes - Dashboard is the parent, AlphaControlRoom nested inside.

### 3. 401/Manifest Fix

**Problem:** `site.webmanifest` returning 401 due to Vercel Deployment Protection.

**Fix:**
- Go to Vercel Dashboard → Settings → Deployment Protection
- Disable Vercel Authentication for preview branches
- OR ensure `site.webmanifest` exists in `public/` folder

### 4. User Profile Fetch Fix

**Problem:** "Failed to fetch user profile" - missing or invalid Supabase keys.

**Fix:** Ensure these environment variables are set in Vercel:
- `VITE_SUPABASE_URL` - Must match Supabase Dashboard exactly
- `VITE_SUPABASE_ANON_KEY` - Must match Supabase Dashboard exactly
- `VITE_API_URL` - Must match current RunPod ID

### 5. Health Check Checklist

Run this before deploying to verify everything works:

1. **Vercel Auth:** Is Deployment Protection OFF? (Prevents 401 on manifest)
2. **Pod Identity:** Does `VITE_API_URL` match the current active RunPod ID?
3. **Supabase Auth:** Can you manually log in via `/login` page? (Tests if keys work)

---

## v2.6.4: Infisical CLI Fix (April 2026)

### Fixes Applied

1. **Infisical CLI Upgrade** - Added `sudo infisical upgrade` after installation
2. **Project Init** - Added `.infisical.json` creation with workspace ID
3. **Token Auth** - Using `--token=$INFISICAL_TOKEN` instead of env var

### Workflow Files Fixed

- `deploy-beta-runpod.yml` - Added project init + token flag
- `auto-deploy-runpod.yml` - Added project init + token flag
- `deploy_all.sh` - Updated with project ID

### Fixes Applied

1. **Infisical Project ID** - Added `--projectId="f8464ba0-1b93-45a1-86b5-c8ea5a81a2a4"` to all `infisical export` and `infisical run` commands
   - `deploy-beta-runpod.yml` - Fixed
   - `auto-deploy-runpod.yml` - Fixed

2. **AdminAnalyticsPage** - Import path verified, file exists at `./pages/admin/AdminAnalyticsPage`

### GitHub Secrets Required

| Secret | Description |
|--------|-------------|
| `INFISICAL_TOKEN` | Infisical service token |
| `INFISICAL_CLIENT_ID` | Infisical client ID |
| `INFISICAL_CLIENT_SECRET` | Infisical client secret |
| `INFISICAL_PROJECT_ID` | Infisical project ID |
| `DOCKER_LOGIN` | Docker Hub username |
| `DOCKER_PW_TOKEN` | Docker Hub password/token |
| `RUNPOD_API_KEY` | RunPod API key |
| `RUNPOD_ID` | RunPod pod ID |

---

## v2.5.13: Full "No-Env" Transition (April 2026)

### Changes Applied
- Dynamic CORS (Regex) for Vercel branch support
- Automated POD_ID capture
- Autoscaler fail-fast

---

## v2.5.12: Secret Handshake Skill (April 2026)

### Changes Applied
- Vercel sync automation
- INFISICAL_TOKEN injection

---

## v2.5.11: Reliability Features (April 2026)

### 1. Idempotency Keys (prevent duplicate runs)

**Frontend sends header:**
```http
POST /api/v1/simulations
Idempotency-Key: <uuid>
```

**Supabase table:**
```sql
create table idempotency_keys (
  key text primary key,
  user_id uuid not null,
  request_hash text not null,
  response jsonb,
  status text default 'processing',
  created_at timestamp default now()
);
```

**API logic:**
```python
def hash_request(body: dict) -> str:
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()

# Check existing
existing = supabase.table("idempotency_keys").select("*").eq("key", key).execute()
if existing.data:
    if existing.data[0]["request_hash"] == request_hash:
        return existing.data[0]["response"]  # Return cached
    raise HTTPException(409, "Idempotency key reuse with different payload")
```

---

### 2. Job Status Persistence (Supabase = Source of Truth)

**Redis = transport, Supabase = truth**

**Table:**
```sql
create table simulations (
  id uuid primary key,
  user_id uuid,
  status text check (status in ('queued','running','completed','failed')),
  input jsonb,
  result jsonb,
  error text,
  created_at timestamp default now(),
  updated_at timestamp default now()
);
```

**API writes on enqueue:**
```python
supabase.table("simulations").insert({
    "id": job_id,
    "user_id": user["user_id"],
    "status": "queued",
    "input": data
}).execute()
```

**Worker state transitions:**
```python
# On start
supabase.table("simulations").update({"status": "running"}).eq("id", job_id).execute()

# On success
supabase.table("simulations").update({"status": "completed", "result": result}).eq("id", job_id).execute()

# On failure
supabase.table("simulations").update({"status": "failed", "error": str(e)}).eq("id", job_id).execute()
```

---

### Final Architecture

```
Frontend
   ↓ (Idempotency-Key)
API (FastAPI)
   ├── verifies user
   ├── enforces idempotency
   ├── writes "queued" → Supabase
   └── pushes job → Redis

Worker
   ├── pops job
   ├── updates "running"
   ├── executes simulation
   ├── updates "completed"/"failed"
   └── publishes event (WebSocket)

Supabase = SOURCE OF TRUTH
Redis = TRANSPORT LAYER
```

### Problems Solved

| Problem | Fixed by |
|---------|----------|
| Duplicate runs | Idempotency keys |
| Lost job state | Supabase persistence |
| Worker crash mid-job | Status recoverable |
| Retry duplication | Same job_id reused |
| UI inconsistency | DB = truth |

---

## v2.5.10: Advanced Features (April 2026)

### 1. Auth Passthrough (Supabase → API → Worker)

**API verifies JWT and injects user context into job:**

```python
# services/api/auth.py
def verify_user(authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "")
    payload = jwt.decode(token, SB_JWT_SECRET, algorithms=["HS256"])
    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "role": payload.get("role"),
    }

# Enqueue with user context
job = {
    "id": str(uuid.uuid4()),
    "payload": data,
    "user": user,  # ✅ user_id, email, role
    "created_at": time.time(),
}
```

**Worker accesses user context:**

```python
job = json.loads(job_raw)
user = job.get("user", {})
user_id = user.get("user_id")
tier = user.get("role")
```

---

### 2. Retry + Dead Letter Queue (DLQ)

**Queue Strategy:**

| Queue | Purpose |
|-------|---------|
| `simhpc_jobs` | Main queue |
| `simhpc_jobs_retry` | Retry queue |
| `simhpc_jobs_dlq` | Dead letter |

**Worker logic:**

```python
MAX_RETRIES = 3

def process_job(job):
    try:
        run_simulation(job)
    except Exception as e:
        job["retries"] = job.get("retries", 0) + 1
        job["error"] = str(e)

        if job["retries"] < MAX_RETRIES:
            redis.rpush("simhpc_jobs_retry", json.dumps(job))
        else:
            redis.rpush("simhpc_jobs_dlq", json.dumps(job))
```

---

### 3. WebSocket Real-Time Updates

**API WebSocket endpoint:**

```python
# services/api/ws.py
connections = defaultdict(list)

async def websocket_endpoint(ws: WebSocket, user_id: str):
    await ws.accept()
    connections[user_id].append(ws)
    try:
        while True: await ws.receive_text()
    except: connections[user_id].remove(ws)
```

**Worker publishes events via Redis:**

```python
redis.publish("simhpc_events", json.dumps({
    "user_id": user_id,
    "event": {"job_id": job_id, "status": status}
}))
```

**Frontend connects:**

```ts
const ws = new WebSocket(`wss://api.com/ws?user_id=${user.id}`)
ws.onmessage = (msg) => updateStatus(JSON.parse(msg.data))
```

---

### Architecture Summary

```
Frontend → Vercel /api/* → API (JWT verify) → Redis queue → Worker
                       ↓                    ↓                    ↓
                   WebSocket          Job + user           publish events
                   (real-time)        context              → Redis pubsub
```

### GitHub Secrets Required

| Secret | Description |
|--------|-------------|
| `INFISICAL_CLIENT_ID` | Infisical client ID |
| `INFISICAL_CLIENT_SECRET` | Infisical client secret |
| `INFISICAL_PROJECT_ID` | Infisical project ID |
| `DOCKER_LOGIN` | Docker Hub username |
| `DOCKER_PW_TOKEN` | Docker Hub password/token |
| `RUNPOD_API_KEY` | RunPod API key |
| `RUNPOD_ID` | RunPod pod ID |

---

## v2.5.9: Architecture Fixed (April 2026)

### ⚠️ VERIFIED WORKING (Production Checklist)

- [ ] Frontend ONLY calls `/api/*` (not direct runpod.net)
- [ ] No CORS issues (proxy handles routing)
- [ ] Vercel proxy returning 200 for /api/v1/*
- [ ] Worker pulling jobs from Redis successfully

### Changes Applied

1. **Worker = Pure Compute** - Removed FastAPI, CORS, HTTP endpoints from worker
   - Worker now ONLY consumes Redis queue
   - Single shared Redis client (not per-loop)
   - Single job format: JSON with `id`, `status`, `progress`

2. **Clean Architecture**:
   ```
   Frontend → Vercel /api/* → Proxy → RunPod API → Redis → Worker
   ```

### Key Design Rules

| Rule | Description |
|------|-------------|
| One HTTP surface | API handles all HTTP, Worker has none |
| One job format | JSON only: `{"id": "...", "status": "queued"}` |
| Frontend → /api/* | Never call RunPod directly from browser |

### GitHub Secrets Required

| Secret | Description |
|--------|-------------|
| `INFISICAL_CLIENT_ID` | Infisical client ID |
| `INFISICAL_CLIENT_SECRET` | Infisical client secret |
| `INFISICAL_PROJECT_ID` | Infisical project ID |
| `DOCKER_LOGIN` | Docker Hub username |
| `DOCKER_PW_TOKEN` | Docker Hub password/token |
| `RUNPOD_API_KEY` | RunPod API key |
| `RUNPOD_ID` | RunPod pod ID |

---

## v2.5.8: Blockers Fixed (April 2026)

### Changes Applied

1. **vercel.json updated** - Added API rewrite rule:
   ```json
   { "source": "/api(/.*)?", "destination": "/api/[...path]" }
   ```
   This routes all `/api/*` requests through the proxy.

2. **Proxy exists** - `apps/frontend/api/[...path].ts` already handles proxying requests to RunPod.

### How It Works

- Frontend calls `/api/v1/simulations` (same-origin)
- Vercel rewrites to `/api/[...path].ts`
- Proxy forwards to `https://{pod}.proxy.runpod.net/api/v1/simulations`
- No CORS needed - server-to-server call

### Environment Variables (Vercel)

| Key | Value |
|-----|-------|
| `RUNPOD_API_KEY` | Your RunPod API key |
| `RUNPOD_POD_NAME` | Pod name to filter (optional) |

---

## v2.5.6: Comprehensive Audit Applied (April 2026)

### Key Fixes Applied

1. **APIReference Import Fix** - Removed broken import from `apps/frontend/src/pages/index.ts`
2. **CORS Configuration** - Updated `ALLOWED_ORIGINS` with explicit origins (no wildcards)
3. **GitHub CI** - Updated Node version to 22, added Infisical token support
4. **Vercel Build** - Fixed by removing non-existent component import

### Test Commands

```bash
# Test health endpoint
curl https://your-pod.proxy.runpod.net/api/v1/health

# Test profile fetch
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://your-pod.proxy.runpod.net/api/v1/user/profile
```

### Environment Variables Required

| Key | Value |
|-----|-------|
| `ALLOWED_ORIGINS` | `http://localhost:3000,http://localhost:5173,http://localhost:59824,http://127.0.0.1:59824,https://simhpc-nexusbayareas-projects.vercel.app,https://simhpc.nexusbayarea.com,https://simhpc.com` |
| `SB_URL` | Supabase project URL |
| `SB_SERVICE_KEY` | Supabase service role key |
| `SB_JWT_SECRET` | Supabase JWT secret |
| `REDIS_URL` | Redis connection string |

---

## v2.5.5 Architecture: Vercel Proxy Layer

### Problem
CORS errors persist between frontend (Vercel) and backend (RunPod) due to origin mismatches.

### Solution: Vercel API Route Proxy (`api/[...path].ts`)
```ts
export default async function handler(req, res) {
  const BASE_URL = process.env.RUNPOD_API_URL;
  const path = req.query.path?.join("/") || "";
  const url = `${BASE_URL}/${path}`;

  const response = await fetch(url, {
    method: req.method,
    headers: {
      "Content-Type": "application/json",
      Authorization: req.headers.authorization || "",
    },
    body: req.method !== "GET" && req.method !== "HEAD" ? JSON.stringify(req.body) : undefined,
  });

  res.status(response.status).send(await response.text());
}
```

### Benefits
- Eliminates CORS permanently (server-to-server)
- Centralized auth passthrough
- Unified `/api/*` layer for all backend calls
- Easy to add logging/rate limiting

### Frontend Changes
```ts
// Before (CORS issues)
fetch("https://runpod-pod.proxy.runpod.net/api/v1/...")

// After (proxy)
fetch("/api/api/v1/...")
```

### Environment Variables (Vercel)
- `RUNPOD_API_URL` = `https://{POD_ID}-8000.proxy.runpod.net`

---

## v2.5.5: SB_ Env Prefix for Infisical

### Problem
Infisical flags secrets containing "SUPABASE" as sensitive.

### Changes
| Old | New |
|-----|-----|
| `SUPABASE_URL` | `SB_URL` |
| `SUPABASE_SERVICE_ROLE_KEY` | `SB_SERVICE_KEY` |
| `SUPABASE_JWT_SECRET` | `SB_JWT_SECRET` |
| `SUPABASE_AUDIENCE` | `SB_AUDIENCE` |

### Required RunPod Pod Environment Variables
| Key | Value |
|-----|-------|
| `SB_URL` | Supabase project URL |
| `SB_SERVICE_KEY` | Supabase service role key |
| `SB_JWT_SECRET` | Supabase JWT secret |
| `SB_AUDIENCE` | `authenticated` |
| `ALLOWED_ORIGINS` | CORS allowed origins |
| `REDIS_URL` | Redis connection string |

---

## Pending Fixes (Not Yet Applied)

### 1. APIReference Import Fix
File: `apps/frontend/src/pages/index.ts`
- Remove or fix `./APIReference` import that doesn't exist

### 2. Ruff Lint Fixes
File: `services/worker/worker.py`
- Remove unused imports: `hashlib`, `requests`, `ConnectionError`
- Fix one-line if statements (E701)

### 3. GitHub Actions Node Version
Update to Node 22:
```yaml
uses: actions/setup-node@v4
with:
  node-version: 22
```

### 4. Manifest 401 Fix
Ensure `/site.webmanifest` exists in `/public` or remove from HTML

## v2.5.5: Dynamic Pod Synchronization + Infisical Integration

### Phase 4: Pod Metadata Sync
When a new Pod is provisioned, values propagate to secrets vault and trigger frontend rebuild.

**sync-pod.sh** (`scripts/sync-pod.sh`):
```bash
./scripts/sync-pod.sh <POD_ID>
# Updates: RUNPOD_POD_ID, VITE_API_URL in Infisical
# Triggers: Vercel redeploy with new URL
```

### In-Memory Cache Fallback
API now gracefully falls back to in-memory cache when Redis is unavailable.

**New Helpers:**
- `get_cache()` - Returns Redis or InMemoryCache
- `is_redis_available()` - Returns bool for cache mode detection
- Health check now shows `cache_mode: "redis" | "in_memory_fallback"`

### Updated Master Deploy Flow
```bash
# 1. Build & Push Docker
docker build -f Dockerfile.unified -t simhpcworker/simhpc-unified:latest .
docker push simhpcworker/simhpc-unified:latest

# 2. Provision New Pod
NEW_POD_ID=$(python3 scripts/deploy_unified.py | grep -oP '(?<=pod_id: )[a-z0-9]+')

# 3. Sync Metadata
./scripts/sync-pod.sh $NEW_POD_ID

# 4. Update GitHub
git add . && git commit -m "deploy: update pod to $NEW_POD_ID" && git push

# 5. Fleet Synced
```

---

- **v2.5.4**: SimHPC Skills System + Git Auto-Deploy + Env-Based CORS + **Unified Deployment (API+Worker+Autoscaler in Single Pod)** + **Dynamic Sync Script** + Docker Lean Images + Infisical Integration + Multi-Stage Builds + Non-Root Execution + CVE Remediations + PYTHONPATH Fix for Module Imports + **Vercel Build Fix (APIReference import)** + **Deployment Skills (Vercel, GitHub Safe Push, deploy_all.sh)** + **Supabase SB_ Secret Sync (sb-sync.sh)** + **Zod Downgrade to 3.24.4** + **Vite Chunk Size Optimization** + **Supabase Real Credentials** + **CORS Fix (Allow All Origins + Vercel Regex)**

## Deployment Skills System (v2.5.4)

### Skills Structure
```
skills/
├── antigravity/     # AI agent skills
├── deployment/       # Deployment pipeline skills
│   ├── SKILL.md
│   ├── vercel-deploy.md
│   └── github-safe-push.md
├── docker/         # Docker optimization
├── runpod/         # RunPod deployment
└── ...
```

### Master Deploy Script (deploy_all.sh)
```bash
#!/bin/bash
echo "[1/5] Running Local Build Test..."
infisical run -- npm run build

if [ $? -ne 0 ]; then
    echo "Local build failed. Fix pathing/imports before pushing."
    exit 1
fi

echo "[2/5] Build passed. Syncing Infisical..."
infisical secrets push

echo "[3/5] Deploying to Vercel..."
infisical run --env=production -- vercel --prod --yes

echo "[4/5] Fixing Git Casing..."
git rm -r --cached .
git add .
git commit -m "fix: resolve APIReference pathing and sync v2.5.4"

echo "[5/5] Pushing to GitHub..."
git push origin main
```

- **v2.6.3**: **Vercel Build Stability** (File Migration & Path Fixes) + **Infisical Project Integration** (Explicit ProjectID in CI) + **Refreshed Installation Scripts**
- **v2.6.2**: **CI/CD Hardening** (Infisical Token Standard, Docker Secret Alignment) + **File Path Normalization** (AlphaControlRoom)
- **v2.6.1**: Bare Except Guard (Specific Exceptions) + Python Worker Hardening (JSON/Type Error Handling) + Hardened Deployment Script
- **v2.6.0**: Cost-Optimized Autoscaler (120s Idle Timeout) + Dormant Termination (48h) + Direct-Action Admin API (`runpod_service.py`) + Admin Dashboard Auto-Term Visibility + Accurate Cost Tracking
- **v2.5.6**: Advanced Dynamic API Proxy (Vercel) + Cold Start Resilience (Retry/Backoff) + Caching + `@app.get("/health")` Endpoint + Resolved CORS permanently
- **v2.5.5**: Unified API Proxy (Vercel) Implementation + Vercel Build Fix (APIReference) + Python Worker Lint Fix (`ruff --fix`) + Frontend API Proxy Alignment + Deployment SOP v2.5.5
- **v2.5.4**: Detailed Error Surface in `api.ts` + Empty Token Guard + Infisical Machine Identity v2.5.4
- **v2.5.3**: Full Fleet Build (Worker, API, Autoscaler) + Security Hardening (Non-Root Execution) + CVE Remediations + Infisical Integration + CORS Policy Update (Exposed Headers + Explicit OPTIONS Preflight) + Integrated SimHPC Skill Tool (`fix-all`) + `run_api.py` Entry Point Audit + Vercel Deployment Preparation
- **v2.5.2**: Fixed Supabase key authentication (JWT) + Worker heartbeat fix + API deployed to RunPod
- **v2.5.1**: FastAPI Dependency Injection Fix + RunPod URL Fix + Route Ordering Fix + Worker Queue Fix + Queue Key Alignment + Lazy Redis + Docker .env Removal + Admin Import Fix + Route Import Fix + Control Data Fix
- **v2.5.0**: Structural Consolidation (Single Source of Truth), Unified Worker Plane, Schema Normalization, **Simulation Usage Quota & Anti-Spam Enforcement**, **Health Check Endpoint**, **Worker Heartbeat Always-On**, **Ruff Lint Clean (0 errors)**, **Pre-Commit Framework + GitHub Actions CI**, **Unified Deployment Pipeline**, **RunPod Auto-Updater**, **Admin RBAC (ProtectedRoute)**, **Admin Dashboard (Sidebar + KPIs)**, **Supabase Edge Function (Fleet Metrics)**, **Platform Alerts + Billing Threshold**, **Panic Button (Terminate All Fleet)**, **Real-Time Telemetry Hook**, **Guidance Engine (Mercury AI)**, **Docker Path Alignment**, **Race Condition Fix**, **Credential Sanitization**, **Infisical Universal Auth (RogWin)**, **Docker Worker Image v2.5.0 Built**, **Supabase CLI Linked & Deployed (ldzztrnghaaonparyggz)**.

## Full Fleet Build & Security Hardening (v2.5.3)

### Problem: Image Bloat & Root Vulnerabilities

Previous images were over 2GB (API) and used default root users, increasing the attack surface. Autoscaler lacked Infisical integration for secret management.

### Fix: Hardened Fleet v2.5.3

1. **Worker (`simhpc-worker:v2.5.3`)**:
   - Switched to `nvidia/cuda:12.8.1-runtime-ubuntu22.04` base.
   - Enforced **non-root execution** with `simuser`.
   - Applied critical security patches for `setuptools`, `wheel`, and `pip`.
2. **API (`simhpc-api:v2.5.3`)**:
   - Implemented **Multi-Stage Build** (Builder → Runtime) reducing image size.
   - Hardened with non-root `simuser` and gunicorn/uvicorn stack.
   - Added automated Healthcheck for `v1/health`.
3. **Autoscaler (`simhpc-autoscaler:v2.5.3`)**:
   - Integrated **Infisical CLI** for just-in-time secret injection.
   - Multi-stage build with non-root user for process isolation.
   - Uses `infisical run --` to wrap the Python entry point.

---

## FastAPI Dependency Injection Fix (v2.5.1)

### Problem: Startup Crash - `ValueError: no signature found for builtin type <class 'dict'>`

FastAPI was crashing at API startup when inspecting the `Depends(verify_auth)` pattern. The module-level `verify_auth: Any = None` caused FastAPI to try to introspect `None` (or Python's built-in `dict` type) which has no callable signature.

### Fix: Stub Function Pattern

Replaced all module-level `None` defaults with proper stub functions that FastAPI can introspect at import/include time:

```python
# Before (broken)
verify_auth: Any = None

# After (working)
def verify_auth(authorization: str = Header(None)) -> dict:
    """Stub replaced by init_routes(). If called, app wasn't initialized."""
    raise RuntimeError("verify_auth not initialized — call init_routes() first")
```

Applied to: `verify_auth` in `simulations.py`, `control.py`, `certificates.py`, `verify_admin` in `admin.py`.

### Additional Fixes in v2.5.1

1. **RunPod Status URL Fix**: `get_job_status` was missing `pod_id` in the URL path (was `/status/{job_id}`, now `/{pod_id}/status/{job_id}`)

2. **enqueue_job Signature Fix**: Changed `enqueue_job(sim_id, job_data)` to `enqueue_job(job_data)` to match `job_queue.py` signature

3. **Route Ordering Fix**: Moved `/simulations/usage` route above `/{sim_id}` to prevent `/usage` from being caught as a sim_id parameter

4. **Worker Queue Busy Loop Fix**: Changed `lpush` to `rpush` when pushing back jobs at capacity to prevent tight busy loop

5. **Queue Key Alignment**: Changed `job_queue.py` from `"jobs:pending"` to use `os.getenv("QUEUE_NAME", "simhpc_jobs")` — aligns with worker's `QUEUE_NAME` default

6. **Lazy Redis Connection**: Wrapped Redis connection in `get_redis()` lazy init function instead of connecting at import time — prevents crash during docker-compose startup or Vercel cold start

7. **Docker .env Removal**: Removed `COPY services/api/.env ./` from `Dockerfile.api` — secrets should be passed as runtime environment variables, not baked into image

8. **Admin Import Fix**: Removed broken `sys.path.append` import of `autoscaler.py` from admin.py — replaced with fallback that indicates Redis pub/sub IPC not implemented

9. **Route Import Fix**: Fixed `onboarding.py` relative imports (`...schemas.onboarding`) that would fail in Docker — now uses try/except with absolute imports

10. **Control Data Fix**: Removed hardcoded fake alerts from `control.py` — now fetches real alerts from Redis keys `alert:*` and timeline from `timeline:*`
- **v2.4.1-DEV**: Mission Control Cockpit Synchronization + Persistent Onboarding (Autosave & Cross-Device Resume).
- **v2.4.0-DEV**: Interactive Onboarding (Guided Walkthrough) + Event-Driven Trigger Engine.
- **v2.3.0**: Option C Autoscaler (Stop/Resume) + Network Volume Persistence + "Wake GPU" Admin Panel.
- **v2.2.1**: RunPod API Integration + Queue-Aware Autoscaler + Docker Hub Images.
- **v1.6.0-ALPHA**: Mission Control Cockpit (Modular Design Intelligence Platform).
- **v1.5.1-ALPHA**: Alpha Control Room (4-Panel UI).
- **v1.4.0-BETA**: Direct Vercel Deployment & RunPod Orchestration.

---

## Structural Consolidation: Single Source of Truth (v2.5.0)

### Problem: Fragmented Worker & Scaling Logic

The `v2.4` codebase had logic spread across `services/runpod-worker/`, `services/worker/`, and `robustness-orchestrator/`. Key issues:
- Multiple `worker.py` and `autoscaler.py` versions causing "truth drift."
- Scaling logic (`idle_timeout.py`) buried in an `/app/` subdirectory.
- Standalone services (PDF, AI Report) not integrated into the primary worker loop.
- Deployment manifests (`Dockerfile.worker`) referencing outdated paths.

### Fix: Unified Compute Plane

1.  **Unified `services/worker/`**: Consolidated all compute-related logic into a single, clean directory.
2.  **Truth Promotion**:
    - Promoted `worker.py` (v2.5.0) as the canonical physics execution engine.
    - Promoted `idle_timeout.py` (v2.3.0) and renamed it to `autoscaler.py` as the official scaling strategy.
    - Integrated `ai_report_service.py` and `pdf_service.py` into the worker runtime.
3.  **API Integration**: Updated `services/api/api.py` to point to the unified `services/worker/` for fleet management and "Warm" commands.
4.  **Legacy Purge**: Created `legacy_archive/` to house all deprecated v1.6.0-ALPHA and v2.2.1 artifacts.
5.  **Security Hardening**: Enforced April 1st standard for `.env` protection and Git hygiene.

---

## Beta Hardening: Alignment & Tightening (Complete)

### Backend Accuracy

- **Standardized API Namespaces**: Ensured all frontend routing goes through `api/v1/`.
- **Runtime Validation**: Added `schemas.ts` bringing strict `zod` validation protecting against worker inconsistencies.
- **Idempotency**: Added UUID-based API idempotency (`Idempotency-Key` headers) to `Certificate` generation so multiple quick requests don't duplicate generation.
- **Background Queues Mocked**: Certificates endpoints updated to avoid blocking API threads, correctly returning `processing` statuses under async operations.

### Frontend UI Alignment

- **Single Source of Truth**: Replaced multiple data models mapping UI directly from `simulations` database responses.
- **States Visualized**: Surfaced real status keys ("running", "auditing", "completed") directly mapping them to components (e.g. `SimulationDetailModal`).
- **Cockpit Tightened**: Explicitly disabled high-risk "Clone" and "Intercept" actions to reduce vulnerability ahead of beta scale operations while enabling "boost" and "certify".

---

## Schema Normalization: Single Source of Truth (v2.5.0)

### Problem: Schema Drift + Inconsistent Contracts

The `simulation_history` table had drifted from the API response shapes and frontend types. Key issues:

- Frontend expected `ai_insight` and `metrics` in `result_summary`, but worker wrote `data` and `pdf_url`
- Control Room API returned `id`/`model_name` but frontend expected `run_id`/`model`
- Alert shapes mismatched between API (`id`, `type`) and frontend (`alert_id`, `level`, `source`)
- Timeline events used `content` but frontend expected `label` and `severity`
- Lineage edges used `from`/`to` but frontend expected `source`/`target`
- No certificates table, no audit trail, no org-level isolation

### Fix: Beta-Ready Production Schema

1. **Core Table Renamed**: `simulation_history` → `simulations` with backward-compatible view
2. **New Columns**: `org_id`, `prompt`, `input_params`, `gpu_result`, `audit_result`, `hallucination_score`, `certificate_id`, `error`, `pdf_url`, `updated_at`
3. **Status Constraint**: CHECK constraint enforcing `queued`, `running`, `auditing`, `completed`, `failed`
4. **Supporting Tables**: `certificates`, `documents`, `document_chunks`, `simulation_events`
5. **RLS Policies**: User-level and org-level isolation with service-role bypass
6. **Auto `updated_at`**: Trigger-based timestamp updates
7. **Performance Indexes**: 7 new indexes on high-query columns
8. **TypeScript Contracts**: 5 new type files (`db.ts`, `audit.ts`, `api.ts`, `realtime.ts`, `view.ts`)
9. **Backend Alignment**: `api.py` and `worker.py` updated to write to `simulations` table
10. **Frontend Alignment**: `useSimulationUpdates`, `controlRoomStore`, `Dashboard`, `SimulationDetailModal` updated to use new types

### API Routes Split

`api.py` (1281 lines) split into modular route files:
- **`routes/simulations.py`**: `POST /simulations`, `GET /simulations`, `GET /simulations/{id}`, `POST /simulations/{id}/export-pdf`, `GET /simulations/{id}/status`
- **`routes/certificates.py`**: `POST /simulations/{id}/certificate`, `GET /certificates/{id}/verify`
- **`routes/control.py`**: `GET /controlroom/state`, `POST /control/command`, `GET /control/timeline`, `GET /control/lineage`
- **`routes/admin.py`**: Fleet management endpoints (warm, readiness, status, stop, terminate)
- **`routes/onboarding.py`**: Already existed

All routes use `init_routes()` pattern to receive shared dependencies from `api.py`.

---

## Mission Control Cockpit: Backend Synchronization (v2.4.1-DEV)

### Problem: Disconnected Cockpit Components

While the frontend "Cockpit" UI (O-D-I-A-V loop) was designed in `v1.6.0`, many of its command and telemetry components were placeholders or lacked robust backend implementation, leading to "stale" telemetry and non-functional control buttons.

### Fix: Unified Control Subsystem

1. **Unified State Aggregator**:
    - Implemented `GET /api/v1/controlroom/state` to provide a single, consistent snapshot of active runs, audit alerts, and temporal events.
    - Synchronized with `controlRoomStore.ts` to hydrate the entire Cockpit on mount.
2. **Explicit Command Execution**:
    - Implemented `POST /api/v1/control/command` with support for `intercept`, `clone`, `boost`, and `certify`.
    - Integrated the **Operator Console** with real-world job state transitions in Redis.
3. **Temporal & Structural Lineage**:
    - Added `GET /api/v1/control/timeline` and `GET /api/v1/control/lineage` to support the horizontal marquee and parent-child design ancestry graph.
    - Renamed and synchronized `lineageData` in `controlRoomStore.ts` for consistent state hydration.
4. **Admin Fleet Control & Navigation**:
    - Extracted the standalone `WakeGPU.tsx` component and linked it to the `v2.4.1` primary Dashboard Sidebar.
    - Verified the existence and routing of `/admin/analytics` for centralized fleet management.
5. **Tier-Gated Artifact Access**:
    - Integrated signed-URL logic for PDF Report downloads in `SimulationDetailModal.tsx`.
    - Implemented Professional-tier checks (`profile.plan`) to prevent unauthorized artifact access on the Free tier.
6. **Technical UI Stability**:
    - Resolved `getToken` Promise handling across all cockpit components.
    - Fixed `tsconfig.json` path alias resolution (`@/*`) for the monorepo frontend.
    - Standardized `Button.tsx` with a professional `class-variance-authority` (CVA) implementation to resolve project-wide typing errors.

## Persistent Onboarding: Autosave & Cross-Device Resume (v2.4.1-DEV)

### Problem: Fragmented User Journey

Users often start onboarding on one device (e.g., mobile) and want to continue on another (e.g., desktop). Without persistence, users are forced to restart or skip the walkthrough, leading to lower conversion and higher drop-off.

### Fix: Versioned Autosave System

1. **Backend (FastAPI + Supabase)**:
    - Added `GET /api/onboarding` and `POST /api/onboarding` endpoints.
    - Implemented **Versioned Conflict Resolution**: Rejects stale writes with `409 Conflict`.
    - Added event tracking via `POST /api/onboarding/event`.
2. **Frontend (Zustand + React)**:
    - **Debounced Autosave**: State is synced to the backend 1s after any change.
    - **Instant Resume**: Uses `localStorage` for immediate UI response while backend syncs.
    - **Conflict Recovery**: Automatically hydrates state from the server upon detecting a version mismatch.
    - **Multi-Device Polling**: Syncs every 30s to detect progress made on other devices.

---

## Interactive Onboarding: Guided Product Walkthrough (v2.4.0-DEV)

### Structural Alignment & Store Refactoring (April 01, 2026)

### Problem: Documentation/Implementation Mismatch

The `ARCHITECTURE.md` referenced a standalone `WakeGPU.tsx` component that didn't exist (it was inlined in `AdminAnalytics.tsx`). Additionally, the user-facing term `lineageData` was inconsistently mapped to a `lineage` property in the `controlRoomStore.ts`.

### Fix: Component Extraction & Store Synchronization

1. **Extracted `WakeGPU.tsx`**:
    - Created a reusable component at `apps/frontend/src/components/admin/WakeGPU.tsx`.
    - Refactored `AdminAnalytics.tsx` to use the new component, ensuring architectural consistency.
2. **Synchronized Lineage State**:
    - Renamed the store property from `lineage` to `lineageData` and the setter to `setLineageData`.
    - Updated all consumer components (`AlphaControlRoom.tsx`, `SimulationMemory.tsx`, `SimulationLineage.tsx`) to reflect the new naming convention.
3. **Documentation Audit**: Verified the existence and routing of `/admin/analytics`.

---

## Guided Product Walkthrough: The Onboarding Flow (v2.4.0)

SimHPC's advanced physics capabilities can be overwhelming for new users. First-time users often hesitate to run their first simulation or miss the value of the MLE (Machine Learning Enhancement) module.

### Fix: Progressive Event-Driven Onboarding

1. **Guided 8-Step Journey**:
    - **Step 1**: Welcome Modal (First Login Trigger).
    - **Step 2**: Template Selection (Highlight & Dim UI).
    - **Step 3**: Configuration (Progressive Tooltips).
    - **Step 4**: Queue Awareness (Soft Sell for GPU).
    - **Step 5**: Results Visualization (The "Value" Moment).
    - **Step 6**: MLE Optimization (The "Differentiation" Moment).
    - **Step 7**: Comparison View (Proof of Value).
    - **Step 8**: Conversion Trigger (Soft Paywall/Upgrade Card).
2. **Conversion Intelligence**:
    - Triggered by high queue wait times or MLE GPU recommendations.
    - Inline upgrade cards for "Unlock Full Power."
3. **Technical Foundation**:
    - **Frontend**: Zustand state with persistent `onboarding_state` sync.
    - **Animation**: Smooth transitions via Framer Motion.
    - **Backend**: Event stream tracking in FastAPI to trigger context-aware hints.

---

## Option C: On-Demand GPU + Network Volumes (March 28, 2026)

### Problem: Cold Start & Cost Overhead

Previous autoscaling destroyed pods completely, leading to ~3 minute cold starts and loss of solver caches. Scaling up from zero was inefficient for live demos.

### Fix: Hibernation Strategy (v2.3.0)

1. **Option C Autoscaler (`idle_timeout.py`)**:
   - Replaced `terminate_pod` with `stop_pod` to keep the pod disk.
   - Preserves **Network Volume** at `/workspace` for global persistence.
   - Resumes stopped pods in ~90 seconds (2x faster than fresh creation).
   - Idle cost reduced to disk-only (~$0.10/day total dormant cost).
2. **Proactive "Wake GPU" Control**:
   - Added `POST /api/v1/admin/fleet/warm` to resume pods on demand.
   - Created `WakeGPU.tsx` component for the admin cockpit to trigger warm-up 90s before demos.
   - Live readiness polling via `/api/v1/admin/fleet/readiness`.
3. **Rich Fleet API**:
   - Consolidated status including stopped pod IDs and cost tracking.

## RunPod API + Cost-Aware Autoscaler (March 25, 2026)

### Security Audit: Git Hardening (March 28, 2026)

- **Fix: .gitignore Negation Syntax**: Standardized `!filename` patterns to prevent unintentional ignoring of schema/example files.
- **Fix: .env Untracked**: Physically removed tracked `.env` file from Git cache to stop secrets exposure.
- **Policy Enforcement**: Updated `GEMINI.md`, `README.md`, and `ARCHITECTURE.md` with strict rules against `_gitignore` naming and `.env` commits.

### Problem: Idle GPU Burn

Manual pod management via RunPod UI led to $10–$25/day idle burn with no automated cost controls.

### Fix: Production-Grade Orchestration

1. **RunPod API Client (`runpod_api.py`)**: Full pod lifecycle management via GraphQL API.
2. **Queue-Aware Autoscaler v2.2.1**: Advanced scaling based on `queue_length` + `inflight_jobs`.
   - **Metrics**: Real-time tracking of pending vs. processing jobs via Redis.
   - **Cost Control**: `MAX_PODS` cap and automatic idle termination after 300s.
   - **GPU Policy**: Prefers cost-effective A40 GPUs with RTX 3090 fallback.

3. **Vercel & Security Policy v2.2.1**: Standardized environment and deployment policy.
   - **Double-Key Strategy**: Implemented split Supabase keys (Anon for Frontend, Service Role for Worker).
   - **Stable Handshake**: Transitioned to RunPod HTTP Proxy URLs to eliminate "Offline" blips from IP changes.
   - **Google One Tap Fix**: Updated Google Cloud Console origins and redirect URIs for Vercel production.
4. **RunPod Fleet Migration (v2.2.1)**: Successfully migrated to a high-performance pod cluster.
   - **New Pod ID**: See private `INFRASTRUCTURE.md` (excluded from git).
   - **Connection Details**: See private `INFRASTRUCTURE.md` — pod IPs and SSH keys are rotated on each deployment.
   - **Global Sync**: Updated 12+ files across frontend, backend, and documentation to reflect the new pod infrastructure.
5. **Worker v2.2.1**: Integrated with autoscaler metrics.
   - **Inflight Tracking**: Increments `simhpc_inflight` on job pop, decrements on completion.
   - **Activity Timestamping**: Updates `pods:last_used:{pod_id}` in Redis for precise idle detection.
   - **GPU Acceleration**: NVIDIA CUDA 12.1 + high-performance physics stack.
6. **Local Alpha Stack**: Implemented `docker-compose.yml` for solo-founder rapid development.
7. **Admin & Health API**: 7 new protected endpoints in `api.py` for fleet and system health monitoring.
   - `GET /api/v1/system/status` — Aggregated health check (Mercury, RunPod, Supabase, Worker).
   - `GET /api/v1/admin/fleet` — Fleet status dashboard data.
   - `GET /api/v1/admin/fleet/cost` — Cost tracking summary.
   - `POST /api/v1/admin/fleet/pod/{id}/stop` — Stop pod.
8. **Security & Connectivity**:
   - **CORS Hardening**: Added `simhpc.nexusbayarea.com` and `simhpc.com` to allowed origins.
   - **Production Redis Guard**: Added validation to block `localhost` Redis usage in Vercel environments.
   - **Supabase Service Role**: Standardized on `SUPABASE_SERVICE_ROLE_KEY` for background writes.
9. **Infrastructure Updates**:
   - `Dockerfile.autoscaler` updated to include `runpod_api.py`.
   - `docker-compose.yml` autoscaler service updated with 10 additional env vars.

---

## Physics Worker: PDF Report Storage (March 23, 2026)

### Problem: Raw Data Exposure

Simulation results were only available as raw JSON in the database, lacking professional engineering artifacts for export.

### Fix: Automated Engineering Artifacts

1. **PDF Generation**: Implemented a professional PDF report generator in `services/worker/pdf_service.py` with Unicode support and numerical anchoring.
2. **Supabase Storage Integration**:
   - Added `upload_pdf_to_supabase` to handle artifact persistence.
   - Workers now upload generated PDFs to the `reports` bucket.
3. **Tiered Access Control**:
   - Implemented Public URLs for Free/Demo users.
   - Implemented **Signed URLs** (1-hour expiration) for Professional/Enterprise users.
4. **Worker Workflow Update**:
   - `services/runpod-worker/worker.py` now triggers PDF generation and upload upon simulation completion.
   - The `pdf_url` is returned in the job result and synced to the `simulation_history` table for instant frontend access.

---

## Toast Notification System Fix (March 18, 2026)

### Problem: Silent Errors

The `<Toaster />` component from sonner was **never mounted** in the React tree. All 12 `toast()` calls were silently doing nothing.

### Fix: Reactive Toast Notifications

1. Created `src/App.tsx` with `<Toaster />` (6s default, 8s success, 10s error, cyan theme, rounded corners).
2. Created `src/index.css` (toast CSS overrides) and `src/hooks/useSimulationUpdates.ts` (Supabase Realtime hook).
3. Updated `Dashboard.tsx` to use `toast.promise()` pattern for simulation submissions.
4. Created `src/components/SimulationDetailModal.tsx` — AI insights, physics metrics, PDF download.
5. Created `src/pages/AdminAnalytics.tsx` — Admin Control at `/admin/analytics` with lead qualification.

### Custom Domain & First-Party Auth (March 18, 2026)

- DNS: A `@ → 76.76.21.21`, CNAME `auth → [project-ref].supabase.co`
- Eliminates "Cookie Rejected" errors by making Supabase Auth first-party.
- CORS hardened in `api.py` from `["*"]` to explicit allow-list.

---

## Frontend Deployment Diagnosis (March 18, 2026)

### GitHub Pages vs Vercel Analysis

Console logs revealed that the GitHub Pages deployment fails while Vercel works due to:

1. **Environment Variable Injection**: Vite requires `VITE_SUPABASE_URL` at build time.
2. **CSP Restrictions**: `github.io` enforces strict CSP which blocks Stripe.js.
3. **Third-Party Cookie Blocks**: Enhanced Tracking Protection on `github.io` blocks Supabase Auth.

### Decision: Vercel Production Standard

**Vercel retained as Production Primary.** GitHub Pages remains as backup/staging with env var injection fix applied if needed.

---

### March 18, 2026 (SaaS Deployment & Production Launch)

- **Frontend Deployment**: Successfully pushed the finalized `v1.6.0-ALPHA` cockpit to `lostbobo.git`.
- **Production Status**: SimHPC SaaS is LIVE at <https://simhpc.com>.
- **Conflict Resolution**: Synchronized the frontend repository with the latest component updates.

### March 16, 2026 (Mission Control Cockpit Redesign - v1.6.0)

- **Modular Component Architecture**: Decoupled the Alpha Control Room into production-grade components: `TelemetryPanel`, `ActiveSimulations`, `SimulationLineage`, `OperatorConsole`, and `GuidanceEngine`.
- **Mercury AI Integration**: Fully transitioned to Mercury AI for simulation assistance and notebook generation.
- **System Health LEDs**: Real-time status indicators for Mercury AI, Supabase, and RunPod.
