# SimHPC Architecture

> Last Updated: April 03, 2026
> Status: **LIVE (v2.5.0)** — Usage Limits & Rate Limiting Active

---

## System Overview

SimHPC is a cloud-native GPU-accelerated finite element simulation platform. The architecture follows a distributed microservices pattern with a **securely isolated frontend** and a **closed-source backend** orchestration layer.

### The "Mission Control" Stack (v2.5.0)

For local development and alpha testing, the platform uses a unified `docker-compose.yml` stack:

| Service | Docker Image | Description |
| :--- | :--- | :--- |
| Redis | `redis:7-alpine` | Job queueing and inter-service messaging |
| Frontend | — (Nginx Alpine) | React/Vite cockpit served via `Dockerfile.prod` with SPA routing |
| API | `simhpcworker/simhpc-api:v2.3.0` | FastAPI-based control plane for AI and fleet management |
| Worker | `simhpcworker/simhpc-worker:v2.5.0` | Unified compute plane (Physics + Reports + Metrics) |
| Autoscaler | `simhpcworker/simhpc-autoscaler:v2.3.0` | Option C: Stop/Resume strategy with Network Volume persistence |

---

## Database Schema (v2.5.0)

### Core Table: `simulations`

Single source of truth for all simulation state. Replaces the legacy `simulations` table (now a backward-compatible view).

| Column | Type | Notes |
| :--- | :--- | :--- |
| `id` | UUID | Primary key, auto-generated |
| `user_id` | UUID | FK → auth.users(id) |
| `org_id` | TEXT | Org-level isolation for RLS |
| `job_id` | TEXT | Unique, links to Redis job hash |
| `scenario_name` | TEXT | Human-readable label |
| `status` | TEXT | CHECK: `queued`, `running`, `auditing`, `completed`, `failed` |
| `prompt` | TEXT | Natural language input |
| `input_params` | JSONB | Simulation configuration |
| `result_summary` | JSONB | Worker output data |
| `gpu_result` | JSONB | Raw GPU solver output |
| `audit_result` | JSONB | Full Rnj-1 audit (flags, score, anomalies) |
| `hallucination_score` | FLOAT | Extracted from audit_result |
| `report_url` | TEXT | Legacy PDF link |
| `pdf_url` | TEXT | Canonical PDF link |
| `certificate_id` | TEXT | FK → certificates(id) |
| `error` | TEXT | Failure message |
| `created_at` | TIMESTAMPTZ | Auto-set |
| `updated_at` | TIMESTAMPTZ | Auto-updated via trigger |

### Supporting Tables

| Table | Purpose |
| :--- | :--- |
| `certificates` | Verification hashes + storage URLs for compliance certs |
| `documents` | RAG source documents (org-scoped) |
| `document_chunks` | Vector-embedded text chunks (pgvector 768-dim) |
| `simulation_events` | Append-only event log for audit trail |
| `worker_heartbeat` | Worker health pings (existing) |
| `leads` | Lead qualification funnel (existing) |
| `onboarding_state` | User onboarding progress (existing) |
| `demo_access` | Magic link demo tokens (existing) |

### TypeScript Type Locations

| File | Purpose |
| :--- | :--- |
| `src/types/db.ts` | Exact Supabase schema mirror |
| `src/types/audit.ts` | Audit + verification types |
| `src/types/api.ts` | API response contracts |
| `src/types/realtime.ts` | Supabase realtime partial update types |
| `src/types/view.ts` | UI view models + mapper function |

### RLS Policies

- **User-level**: `auth.uid() = user_id` — users see only their own simulations
- **Org-level**: `org_id = auth.uid()::text` — org-scoped access (adjust for team mapping)
- **Service role**: Full access on all tables (for workers and API)

---

## 1. The Physics Worker: Dedicated Pod Architecture (v2.3.0)

### 5. Infrastructure & Storage (March 2026 Stability Updates)

* **Network Volumes (Option C):** A persistent Network Volume is mounted at `/workspace` on GPU pods. This ensures that simulation data, weights, and solver caches persist even when a pod is **STOPPED** to save costs.
* **Shared Scratch Volume:** A `simulation_scratch` volume is mounted at `/tmp/sim_scratch` on both the **API** and **Worker** containers. This allows the API to pass large simulation input files directly to the worker when needed, bypassing Redis for payload efficiency.
* **Security Hardening:** All production Docker images now run as a non-privileged `appuser` to minimize the impact of potential container escapes.
* **Secret Management:** Sensitive keys (Stripe, Supabase JWT, RunPod API, Admin Secret) are managed via Docker Secrets or secure environment variables.
* **Standardized Runtime:** All Python services are standardized on **Python 3.11-slim** to ensure consistent behavior and syntax support across the platform.

---

## 1. The Physics Worker: Dedicated Pod Architecture (v2.3.0)

Unlike the initial pod SimHPC_P_01 prototype, the SimHPC Physics Worker runs as a **long-lived stateful pod** to ensure deterministic physics results and low-latency telemetry.

### A. Redis Polling Mechanism

The `worker.py` script (`services/worker/worker.py`) implements an infinite loop that polls a **Redis list (`simhpc_jobs`)**. This architecture prevents "zombie jobs" and allows the worker to maintain a persistent connection to the simulation environment.

```python
# services/worker/worker.py
while True:
    job_data = redis_client.lpop("simhpc_jobs")
    if job_data:
        with lock:
            active_jobs += 1
        threading.Thread(target=process_job, args=(job,)).start()
```

### B. O-D-I-A-V Decision Loop Orchestration

1. **Observe**: Telemetry from the Pod is pushed to Redis/Supabase.
2. **Detect**: Anomaly detection runs on the API layer.
3. **Investigate**: Historical lineage is pulled from Supabase.
4. **Act**: The operator Intercepts or Clones via the `CommandConsole`.
5. **Verify**: Final certification is written back to the DB.

### 2. Interactive Onboarding & Event-Driven Intelligence (v2.4.0-DEV)

SimHPC implements a progressive, event-driven onboarding layer designed to bridge the gap between complex physics and user value.

#### A. Onboarding Architecture

* **Frontend**:
  * `OnboardingProvider`: Global Zustand state for tracking current step and visibility.
  * `StepRenderer`: Tooltip and Modal engine powered by **Floating UI** and **Framer Motion**.
  * `EventListener`: Hook-based system that listens for specific user actions (e.g., `simulation_started`).
* **Backend**:
  * `onboarding_state`: Persistent PostgreSQL table tracking per-user progress.
  * `trigger_engine`: FastAPI logic that evaluates the `event_stream` to trigger context-aware hints.

#### B. State Model & Persistence (v2.4.1)

SimHPC uses a **Versioned Autosave** strategy to ensure a seamless cross-device experience.

* **Database**: `onboarding_state` table tracks `current_step`, `completed_steps`, `events`, and `version`.
* **Conflict Resolution**: Uses **Optimistic UI with Version Checks**.
  * Backend rejects stale writes (`incoming.version < db.version`) with a `409 Conflict`.
  * Frontend automatically hydrates state from the server upon conflict to maintain consistency.
* **Low-Latency Sync**: Debounced (1s) REST updates for actions, paired with 30s background polling for cross-device resume.

```json
{
  "user_id": "uuid",
  "current_step": "mle_module",
  "completed_steps": ["welcome", "select_template", "configure_sim", "job_queue", "view_results"],
  "events": ["simulation_started", "results_viewed"],
  "skipped": false,
  "version": 6
}
```

#### C. The Value Loop (The "Aha!" Moment)

The onboarding is designed around the **Proof of Value** comparison:

1. Run Simulation (Baseline)
2. Optimize with MLE (Differentiation)
3. Split Screen Comparison (Verification)
4. Conversion Trigger (GPU Acceleration Upsell)

---

## Repository Strategy (Security Posture)

To protect core intellectual property (AI/Physics logic) during the beta phase, the codebase is split:

* **`apps/frontend/`** (Git submodule): Contains the React/Vite application. This directory is a gitlink pointing into `lostbobo.git`. Both the submodule and the parent monorepo share the same remote (`lostbobo.git` → Vercel deployment source). Vercel auto-deploys on push to `lostbobo.git` main.
* **Parent Monorepo (`SimHPC/`)**: Contains the full platform including `robustness-orchestrator`, AI services, and physics-worker configurations. Commits to the monorepo are pushed to `lostbobo.git` main, triggering the Vercel deploy workflow and the RunPod worker deploy workflow.

---

## Project Structure (v2.5.0)

SimHPC v2.5 follows a "Single Source of Truth" directory structure to eliminate redundancy and simplify scaling.

```text
SimHPC/ (Monorepo)
├── apps/
│   └── frontend/            # React/Vite Cockpit (Submodule)
├── services/
│   ├── api/                 # FastAPI Orchestration Layer
│   │   ├── api.py           # Main entry point (v2.4.1)
│   │   ├── auth_utils.py    # JWT & Supabase Auth
│   │   └── demo_access.py   # Magic link system
│   └── worker/              # Unified Compute Plane
│       ├── worker.py        # Unified Physics + Reports (v2.5.0)
│       ├── autoscaler.py    # Option C Hibernation (v2.3.0)
│       ├── runpod_api.py    # RunPod Lifecycle Client
│       ├── requirements.txt # Worker dependencies
│       └── ...              # Physics solvers & services
├── legacy_archive/          # Deprecated v1.6.0-ALPHA artifacts
├── Dockerfile.api           # API container manifest
├── Dockerfile.worker        # Unified Worker container manifest
├── docker-compose.yml       # Local Alpha stack
└── supabase/                # Migrations & RLS policies
```

---

## 1. The Physics Worker: Unified Compute Plane (v2.5.0)

SimHPC v2.5 consolidates all compute, scaling, and reporting logic into `services/worker/`, establishing a high-performance environment for deterministic physics.

### A. Core Components

* **`worker.py`**: The primary execution engine (v2.5.0). It polls the Redis job queue, manages local threading for parallel solvers, generates engineering PDF reports via `fpdf2`, and synchronizes all state with Supabase.
* **`autoscaler.py`**: Implements the **Option C** hibernation strategy (v2.3.0). It monitors the queue length (`pending + inflight`) and proactively stops/resumes GPU pods to maintain a "Warm Fleet" readiness.
* **`runpod_api.py`**: A low-level client for the RunPod GraphQL API, handling pod lifecycle events (create, stop, start, terminate).

### B. Redis Polling Mechanism

The `worker.py` script implements an infinite loop that polls a **Redis list (`simhpc_jobs`)**. This architecture prevents "zombie jobs" and allows the worker to maintain a persistent connection to the simulation environment.

```python
# services/worker/worker.py
while True:
    send_heartbeat()  # Fires every cycle — keeps Dashboard LED Cyan
    job_data = redis_client.lpop("simhpc_jobs")
    if job_data:
        with lock:
            active_jobs += 1
        threading.Thread(target=process_job, args=(job,)).start()
```

### Worker Concurrency Model

**Per-Pod Thread Pool:**

```python
MAX_CONCURRENT_JOBS = int(os.getenv("MAX_CONCURRENT_JOBS", "2"))
active_jobs = 0
lock = threading.Lock()

while True:
    send_heartbeat()  # Keep Dashboard LED Cyan

    with lock:
        if active_jobs >= MAX_CONCURRENT_JOBS:
            time.sleep(1)
            continue

    job_data = redis_client.lpop("simhpc_jobs")
    if job_data:
        with lock:
            active_jobs += 1
        threading.Thread(target=process_job, args=(job,)).start()
```

**Scaling Strategy:**

| Tier | Pods | Max Concurrent Jobs | Max Total Throughput |
| :--- | :--- | :--- | :--- |
| Small | 1 | 2 | 2 jobs |
| Medium | 2 | 2 | 4 jobs |
| Large | 3 | 2 | 6 jobs |

**Scaling Strategy (Option C - Stop/Resume):**

1. Poll queue length (`pending`) and `simhpc_inflight` every `POLL_INTERVAL` seconds.
2. Scale up: `needed = min(MAX_PODS, ceil((pending + inflight) / MAX_JOBS_PER_GPU))`.
3. **Resumption Over Creation**: The autoscaler prefers `STARTING` (resuming) a STOPPED pod rather than creating a new one. This reduces wake-up time from ~3 minutes to ~90 seconds.
4. **Network Volume Persistence**: GPU pods mount a Network Volume at `/workspace`. All physics artifacts persist across stop/start cycles.
5. Scale down: Individual pods are **STOPPED** (not terminated) after `IDLE_TIMEOUT` (300s) of inactivity. This preserves the pod disk at a minimal cost (~$0.01/day).
6. **Fleet API**: Proactive "Warm" capability allows admins to resume pods before a demo via the dashboard.
7. State persisted to Redis (`pods:active` set) + synced against RunPod API each cycle.

### RunPod API Client (`runpod_api.py`)

Production-grade pod lifecycle management using RunPod GraphQL API:

| Function | Purpose |
| :--- | :--- |
| `list_pods()` | Fleet-wide status with GPU utilization and cost estimates |
| `create_pod()` | Programmatic pod creation with MAX_PODS safety cap |
| `start_pod()` | Resume a stopped pod (restarts GPU billing) |
| `stop_pod()` | Pause a pod (stops GPU billing) |
| `terminate_pod()` | Permanently destroy a pod (zeroes billing) |
| `get_fleet_status()` | Aggregated fleet, queue, cost, and scaling state |

All state is persisted in Redis for crash recovery. The autoscaler syncs against the RunPod API each cycle to detect dead/orphaned pods.

### Admin Fleet Management API

Protected by `X-Admin-Secret` header:

| Endpoint | Method | Purpose |
| :--- | :--- | :--- |
| `/api/v1/admin/fleet/status` | GET | Rich fleet status (running, stopped, queue, cost) |
| `/api/v1/admin/fleet/warm` | POST | Proactively resume stopped pods for demos |
| `/api/v1/admin/fleet/readiness` | GET | Check if pods are ready and worker is connected |
| `/api/v1/admin/fleet/cost` | GET | Cost tracking summary |
| `/api/v1/admin/fleet/pod/{id}/stop` | POST | Stop pod (preserve disk) |
| `/api/v1/admin/fleet/pod/{id}/terminate` | POST | Terminate pod (delete disk) |

### Operational MCP Skills (Antigravity)

SimHPC v2.5 introduces native Model Context Protocol (MCP) skills for the Antigravity IDE/CLI, allowing for direct infrastructure and secret management from the AI agent:

*   **`simhpc-ops`**: Real-time fleet metrics (burn rate, active pods) fetched via `get-fleet-metrics` edge function.
*   **`simhpc-secrets`**: Secure synchronization of production environment variables from GCP Secret Manager.
*   **`gcp-vault`**: Secure `gcloud` execution bridge using Infisical for memory-sanitized secret injection (zero-leak policy).
*   **`deploy-guardian`**: Deployment safety gate enforcing Ruff linting and clean-room deployment via Infisical.
*   **`resource-reaper`**: Automated cost-containment tool that terminates "Zombie" GPU pods (RunPod) based on stale Supabase heartbeats (>15m).
*   **`panic-button`**: Emergency shutdown skill (`services/skills/panic_button.py`) — terminates all RunPod pods, logs critical alert to `platform_alerts`.

### Zero-Trust Secret Posture (v2.5.0)

To eliminate the risk of accidental secret exposure and "silent" GPU costs, SimHPC has transitioned to a **Zero-Trust Environment**:

1.  **Infisical Integration**: All high-privilege secrets (GCP, RunPod, Supabase Service Role, `RUNPOD_POD_ID`, `RUNPOD_SSH_KEY`) are injected at runtime via `infisical run --`. Local `.env` files are deprecated in favor of placeholders in `.env.example`.
2.  **Memory Sanitization**: Secrets exist only in memory during command execution and are wiped immediately upon completion.
3.  **Audit-First Deployment**: The `deploy-guardian` enforces a successful linting pass *before* sensitive keys are ever injected for a deployment.
4.  **Automated Financial Shield**: The `resource-reaper` prevents runaway costs by cross-referencing active GPU pods with live heartbeats, automatically killing zombified instances.

#### Frontend Environment Variables (Build-Time Injection)

Vite replaces `import.meta.env.VITE_*` at **build time**, not runtime. This means:

- **Infisical must wrap the build command**: `infisical run --env=prod -- npm run build`
- **Vercel**: Variables must be set in Vercel Dashboard → Project → Settings → Environment Variables (Production)
- **Naming**: Keys MUST be prefixed with `VITE_` to be exposed to the frontend bundle. Non-`VITE_` keys (e.g. `SB_URL`) are invisible to the browser.
- **Zod Schema Validation**: `src/env/schema.ts` defines typed schemas for frontend (`VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_URL`), backend (`REDIS_URL`, `RUNPOD_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`), and full (merged) validation.
- **CI Enforcement**: `scripts/validate-env.ts` runs before every build in CI. Prod mode validates full schema, dev/preview validates frontend only. Build fails immediately with clear error if any variable is missing or malformed.
- **Runtime Safety**: `src/env/client.ts` validates env at module load time, preventing empty strings from ever reaching `createClient()`.

These skills are implemented in `services/skills/` using the `fastmcp` Python framework.

---

## Core Architecture - The O-D-I-A-V Loop (v2.3.0)

SimHPC is built around the **Operational Cockpit** concept, implementing a tight O-D-I-A-V (Observe-Detect-Investigate-Act-Verify) decision loop:

1. **OBSERVE** → `TelemetryPanel` (240Hz solver streams & **Heartbeat Pulse** from RunPod workers).
2. **DETECT** → `AuditFeed` (Rnj-1 AI Auditor anomaly detection).
3. **INVESTIGATE** → `SimulationMemory` (Iteration Lineage & Delta Tracking).
4. **ACT** → `OperatorConsole` (Intercept, Clone, Boost, Certify).
5. **VERIFY** → `GuidanceEngine` (Mercury AI Numerical Anchoring).
6. **DOCUMENT** → Physics-Verified Engineering Reports (PDF).

### Persistence Layer

* **Redis**: Job states, rate limits, telemetry.
* **Supabase**: User data, auth, PostgreSQL, `worker_heartbeat`, `simulations`.
* **Supabase Storage**: Bucket named `reports` for storing engineering PDF reports.
* **Realtime**: `simulations` table allows live toast notifications via `useSimulationUpdates` and live telemetry via `useSimulations` (progress, thermal_drift, pressure_spike).
* **Guidance Engine**: `POST /api/v1/alpha/generate-report/{job_id}` — Mercury AI generates structural health reports from telemetry. Results persisted in `result_summary.ai_report` for cross-session access.
* **Edge Functions**: `get-fleet-metrics` — Supabase Edge Function computes active pods and hourly spend server-side. Admin-only via `app_metadata` role check. Deploy with `supabase functions deploy get-fleet-metrics`. Auto-creates billing alerts when spend > $10/hr (deduplicated per hour).
* **Panic Button**: `trigger-panic-shutdown` — Supabase Edge Function that terminates all RunPod pods and logs a critical alert. Admin-only, double-confirmation required in UI. Deploy with `supabase functions deploy trigger-panic-shutdown`.
* **Platform Alerts**: `platform_alerts` table (migration `004_platform_alerts.sql`) — stores billing, thermal, and system alerts with severity levels. Realtime-enabled for live sidebar notifications.

---

## O-D-I-A-V Loop Walkthrough

SimHPC is designed as an **Operational Cockpit** that facilitates high-stakes engineering decisions through a 6-phase cognitive loop:

1. Observe: Launch baseline thermal simulation and watch real-time telemetry.
2. Detect: Rnj-1 AI Auditor flags any hallucinations or discrepancies.
3. Investigate: Use Simulation Memory and Lineage Tree visualization for root-cause analysis.
4. Act: Execute operator commands via Console (`[INTERCEPT]`, `[CLONE]`, `[BOOST]`).
5. Verify: Guidance Engine validates results against RAG-anchored evidence.
6. Document: Export Physics-Verified Compliance Certificates (PDF) for audit trail.

### System Health & Debugging (v2.5.0)

In the Alpha environment, the Control Room features a real-time `System Status` indicator powered by the **Aggregated Health API (`GET /api/v1/system/status`)**:

* **Mercury AI**: Verified via active chat completions ping to `mercury-2`.
* **RunPod GPU**: Checked via real-time Redis connectivity status.
* **Supabase**: Verified via active client initialization check.
* **Worker**: Checked via **Heartbeat Strategy** (Supabase `worker_heartbeat` table, pinged every cycle by active workers).
* **Security Guard**: API includes a production check that blocks `localhost` Redis usage when running on Vercel to prevent "Offline" blips.
* **Local Debugging**: The repository includes a `.vscode/launch.json` configured for the development server (Port `59824`). Use the **"Launch Chrome (Frontend)"** profile to debug the React application with full source map support.

### Unified Health Check (`GET /api/v1/health`)

The dedicated health endpoint probes all critical dependencies and returns a structured status object:

```json
{
  "status": "healthy",
  "timestamp": "2026-04-02T12:00:00.000000",
  "services": {
    "api": "online",
    "redis": "online",
    "supabase": "online"
  }
}
```

- **`200 OK`**: All services healthy.
- **`503 Service Unavailable`**: One or more services degraded (Redis unreachable or Supabase probe failed).
- **Redis probe**: `r_client.ping()`.
- **Supabase probe**: Lightweight `worker_heartbeat` table query.

---

## Security & Environment Policy (v2.5.0)

### 1. The "Double-Key" Strategy

To balance user security with high-performance worker throughput, SimHPC employs a split Supabase key architecture:

* **Client Plane (Frontend)**: Utilizes `VITE_SUPABASE_ANON_KEY`. Restricted by Row Level Security (RLS) to ensure users can only access their own simulations and profile data.
* **Compute Plane (Worker)**: Utilizes `SUPABASE_SERVICE_ROLE_KEY`. Bypasses RLS to allow the worker to update simulation statuses, upload PDFs, and record heartbeats without per-request user authentication overhead.

### 2. Stable Connectivity (RunPod Proxy)

The production environment uses the **RunPod HTTP Proxy** (mapped to Port 8000 by default) for all API communications.

* **Stable URLs**: Use the RunPod HTTP Proxy URL (per-pod) for a static endpoint that persists across pod restarts.
* **Direct Access**: Pod IPs and SSH keys are managed via the Infisical vault and are rotated per deployment.
* **CORS Hardening**: The API orchestrator explicitly allows requests from `simhpc.com` and Vercel preview domains. The wildcard origin `*` is strictly prohibited in production.
* **Git Security**: Ensure `.gitignore` is correctly named with a leading dot. Never commit `.env` files to version control. If a secret is accidentally committed, use `git rm --cached .env` to untrack it and rotate the keys immediately.
* **Zero-Trust**: Use `infisical run --` for all administrative and deployment tasks. Hardcoded pod IDs and SSH keys are prohibited in tracked files.
### Authentication Flow

1. User signs up/in via Supabase (Magic Link) or Google One Tap.
    * **Google Client ID:** `552738566412-t6ba9ar8jnsk7vsd399vhh206569p61e.apps.googleusercontent.com`
2. Backend verifies JWT via `python-jose`.
3. **Tier Verification:** API queries Supabase `profiles` table to determine `plan_id`.
4. **Persistence:** `simulations` table (Supabase) receives status updates from workers.
5. **Admin RBAC:** `ProtectedRoute` checks `app_metadata.role === 'admin'` on the frontend. Backend admin endpoints protected by `X-Admin-Secret` header.

### Connectivity & CORS

* **Allowed Origins**: Hardened to `simhpc.nexusbayarea.com`, `simhpc.com`, and Vercel preview branches.
* **Environment Sync**: Critical keys (`REDIS_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SIMHPC_API_KEY`) must be synchronized between Vercel and RunPod for full system availability.

### Rate Limiting

* **Login/Signup**: 5 attempts/minute per IP.
* **Simulations (Spam Protection)**: 10s cooldown between runs per user (Redis-enforced).
* **Weekly Quota (Free Tier)**: 10 runs per rolling 7 days (Supabase-enforced).
* **Concurrency**: 1 concurrent, 60s timeout, small mesh only (Free Tier).

---

## Tiered Access Model

| Feature | Free | Professional | Enterprise |
| :--- | :--- | :--- | :--- |
| Simulation runs | 5 max/week | 50/week | Unlimited |
| AI reports | - | ✓ | ✓ |
| PDF export | - | ✓ | ✓ |
| API access | - | - | ✓ |
| High-res grids | 5k nodes | 50k nodes | Unlimited |

---

## Key Services

### RobustnessService

* Handles parameter sampling (±5%, ±10%, Latin Hypercube, Monte Carlo, Sobol).
* Manages baseline caching and input validation.
* Caps concurrent jobs to prevent GPU exhaustion.

### AIReportService

* Mercury AI (Inception Labs) integration for interpretive reports.
* **Role**: Interprets natural language inputs and generates explanatory notebook text.
* **Constraints**: 24-hour TTL cache, scientific tone enforcement.

### PDFService

* FPDF-based PDF generation.
* Matplotlib charts for sensitivity rankings.
* Artifact storage in Supabase Storage with signed URL access.

---

## Deployment Pipeline (v2.5.1)

### Modular CI/CD Workflows

Push to `main` triggers independent, path-aware workflows:

| Workflow | File | Trigger |
|---|---|---|
| **Audit** | `deploy.yml` | All pushes (ruff lint + format) |
| **Worker** | `deploy-worker.yml` | `services/worker/**`, `Dockerfile.worker` |
| **Autoscaler** | `deploy-autoscaler.yml` | `services/worker/runpod_api.py`, `services/worker/autoscaler.py`, `Dockerfile.autoscaler` |
| **Vercel** | `deploy-vercel.yml` | All pushes (frontend build + deploy) |

### Deployment Chain

1. **Audit**: `ruff check` + `ruff format --check` on `services/worker/worker.py` and `services/api/api.py`. Blocks on failure.
2. **Infisical OIDC Auth**: Each deploy job fetches secrets from Infisical using `Infisical/secrets-action@v1.0.15` with OIDC authentication (short-lived tokens, no static credentials).
3. **Deploy Worker**: Build `Dockerfile.worker` → push to `simhpcworker/simhpc-worker:latest`.
4. **Deploy Autoscaler**: Build `Dockerfile.autoscaler` → push to `simhpcworker/simhpc-autoscaler:latest`.
5. **Deploy Vercel**: Build frontend with Vite → deploy to Vercel production.

### Required GitHub Variables (Settings → Actions → Variables)

| Variable | Value | Purpose |
| :--- | :--- | :--- |
| `INFISICAL_PROJECT_SLUG` | *(from project settings)* | Infisical project slug |

### Infisical Integrations (Synced via Dashboard)

| Integration | Connection ID | Sync ID |
| :--- | :--- | :--- |
| GitHub | `cffe0e20-3898-4cc1-bcfb-35cdceab5886` | `06b1f798-0110-4b6c-9a6f-f8cbc9abe662` |
| Supabase | `a9eb6778-af82-4150-9d4f-2c44049e24cd` | `bb23acd6-2ec9-4ce6-a7f5-36a77ea750a4` |
| Vercel | `42c89bfa-3349-4be6-899b-97b2d6e3d461` | `9067124a-8808-4947-867d-c43aec229444` |

### Infisical OIDC Setup

1. Machine identity already exists (`cffe0e20-3898-4cc1-bcfb-35cdceab5886`)
2. **CRITICAL**: In Infisical Dashboard → Project Settings → Machine Identities → Select identity → **Auth Methods** tab → **Add OIDC Auth** with:
   - **Issuer**: `https://token.actions.githubusercontent.com`
   - **Subject**: `repo:NexusBayArea/lostbobo:ref:refs/heads/main`
   - **Audiences**: `https://github.com/NexusBayArea`
3. Verify the identity has read access to `prod` environment secrets
4. Set `INFISICAL_PROJECT_SLUG` as GitHub repo variable (Settings → Actions → Variables)

> **Error "OIDC auth method not found for identity"** means step 2 is not configured. The machine identity exists but has no OIDC auth method — only Universal Auth (client ID/secret). You must add OIDC as an auth method in the Infisical dashboard.

All secrets (`DOCKER_ACCESS_TOKEN`, `DOCKER_USERNAME`, `VERCEL_TOKEN`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, etc.) are fetched from Infisical at runtime via OIDC — no static GitHub secrets needed.

---

## Appendix: Mercury AI Usage in Alpha

Mercury is used as an **assistive layer** in two primary areas:

### 1️⃣ Simulation Setup Assistance

Mercury helps interpret user inputs into simulation parameters.

Example:

```text
User: "simulate high temperature stress"
Mercury -> temperature: 45, duration: 48h, wind: moderate
```

### 2️⃣ Notebook Generation

Mercury writes the **explanatory text** based on solver outputs.

Example:

```text
Results: voltage_drop = 8%, temperature = 42C
Mercury -> "The simulation indicates that elevated temperatures resulted in an 8% voltage drop."
```

### Mercury Health Test (Terminal)

```bash
curl https://api.inceptionlabs.ai/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mercury",
    "messages": [{"role":"user","content":"reply SIMHPC_OK"}]
  }'

```
