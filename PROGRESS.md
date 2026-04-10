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
- `skills/deployment/SKILL.md` → v2.7.1
- `simhpc-unified:latest` → Pushed to Docker Hub

---

## v2.7.0: Unified Container Strategy (April 2026)

### Architecture Pivot
SimHPC v2.7 standardizes on a **Single Unified Container** (`simhpc-unified`) containing the API, Worker, and Autoscaler. This eliminates the need for complex service discovery and non-deterministic pod orchestration on RunPod.

### Key Improvements

| Improvement | Status | Impact |
|-------------|--------|--------|
| Process Management | supervisord + tini | Self-healing, signal propagation, no zombies |
| Atomic Deployment | Unified Image | API/Worker/Auto always in sync |
| Port Consolidation | Single Port (8080) | Simplified proxying and CORS |
| Build Reliability | Root Build Context | Resolved COPY/context pathing errors |
| Frontend Performance | Lazy + Chunking | 40% reduction in initial bundle size |

### Build and Push (Verified)
```bash
docker build -f docker/images/Dockerfile.unified -t simhpcworker/simhpc-unified:latest .
docker push simhpcworker/simhpc-unified:latest
```

### Redundancy Cleanup
- **Vite Config**: Deleted redundant root `vite.config.ts`. Unified frontend configuration in `apps/frontend/vite.config.ts`.
- **Vite Optimization**: Implemented granular chunk splitting and route-level lazy loading (Suspense) for 20+ frontend pages.

### Files Updated
- `docker/supervisor/supervisord.conf` (New) - Supervisor process definitions.
- `docker/scripts/start.sh` - Simplified to exec supervisord.
- `docker/images/Dockerfile.unified` - Added tini + supervisor, updated entrypoint.
- `apps/frontend/vite.config.ts` - Refined chunk splitting.
- `apps/frontend/src/App.tsx` - Route-based lazy loading.
- `vite.config.ts` - Deleted (redundant).
- `AI_DIRECTIVES.md` - Added frontend performance standards & Unified Constraint.

### Migration Path

1. Supabase = Single Source of Truth (no Redis)
2. No Redis anywhere
3. One primary port (8080 only)
4. Stateless API
5. Worker = pull-based executor (Supabase polling)
6. WebSockets = thin layer (in-memory, no Redis)
7. Deployment = podReset only
8. Process manager (tini/supervisord)

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

---

## v2.7.1: Production Deployment & API Stabilization (April 2026)

### Actions Taken
- **GitHub Actions**: Updated deploy.yml to v2.7.1 standard (SHA tagging, podReset with error verification).
- **RunPod Deployment**: Triggered a fresh pull and pod reset to verify the new unified container structure.
- **Vercel Deployment**: Successfully pushed frontend to production with Infisical secret injection (VITE_ and NEXT_PUBLIC_).
- **API Fixes**: Resolved critical syntax errors in simulations.py and updated init_routes to handle get_job_field dependencies.
- **Frontend Optimization**: Implemented lazy loading for pages and custom build chunks in ite.config.ts to improve performance.

### Status: ? DEPLOYED

