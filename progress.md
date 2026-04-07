# Progress Log

> **Note**: This file tracks high-level development milestones and architectural decisions.
> For a detailed, versioned changelog, see [CHANGELOG.md](./CHANGELOG.md).

## Current Status

- **v2.5.3**: Security Hardening (Non-Root Execution) + CVE Remediations + CORS Policy Update (Allow All Origins) + Integrated SimHPC Skill Tool (`fix-all`) + `run_api.py` Entry Point Audit + Vercel Deployment Preparation
- **v2.5.2**: Fixed Supabase key authentication (JWT) + Worker heartbeat fix + API deployed to RunPod
- **v2.5.1**: FastAPI Dependency Injection Fix + RunPod URL Fix + Route Ordering Fix + Worker Queue Fix + Queue Key Alignment + Lazy Redis + Docker .env Removal + Admin Import Fix + Route Import Fix + Control Data Fix
- **v2.5.0**: Structural Consolidation (Single Source of Truth), Unified Worker Plane, Schema Normalization, **Simulation Usage Quota & Anti-Spam Enforcement**, **Health Check Endpoint**, **Worker Heartbeat Always-On**, **Ruff Lint Clean (0 errors)**, **Pre-Commit Framework + GitHub Actions CI**, **Unified Deployment Pipeline**, **RunPod Auto-Updater**, **Admin RBAC (ProtectedRoute)**, **Admin Dashboard (Sidebar + KPIs)**, **Supabase Edge Function (Fleet Metrics)**, **Platform Alerts + Billing Threshold**, **Panic Button (Terminate All Fleet)**, **Real-Time Telemetry Hook**, **Guidance Engine (Mercury AI)**, **Docker Path Alignment**, **Race Condition Fix**, **Credential Sanitization**, **Infisical Universal Auth (RogWin)**, **Docker Worker Image v2.5.0 Built**, **Supabase CLI Linked & Deployed (ldzztrnghaaonparyggz)**.

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
