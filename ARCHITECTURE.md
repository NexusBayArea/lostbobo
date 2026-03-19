# SimHPC Architecture

> Last Updated: March 19, 2026
> Status: **LIVE (v2.1.2)**

---

## System Overview

SimHPC is a cloud-native GPU-accelerated finite element simulation platform. The architecture follows a distributed microservices pattern with a **securely isolated frontend** and a **closed-source backend** orchestration layer.

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   Vercel        │       │   RunPod        │       │   Supabase      │
│ (Frontend Only) │──────▶│ (API + Worker)  │──────▶│ (Auth + DB)     │
│ React + Vite    │       │ FastAPI + Redis │       │ PostgreSQL       │
│ [Public]        │       │ [Pod / Polling] │       │ [Realtime ON]   │
└────────┬────────┘       └────────┬────────┘       └────────┬────────┘
         │                         │                         │
         └─────────────────────────┴─────────────────────────┘
                    Supabase Realtime (simulation_history)
```

---

## 1. The Physics Worker: Dedicated Pod Architecture (v2.0.0)
Unlike the initial serverless prototype, the SimHPC Physics Worker runs as a **long-lived stateful pod** to ensure deterministic physics results and low-latency telemetry.

### A. Redis Polling Mechanism
The `worker.py` script (`services/runpod-worker/worker.py`) implements an infinite loop that polls a **Redis list (`simhpc_jobs`)**. This architecture prevents "zombie jobs" and allows the worker to maintain a persistent connection to the simulation environment.

```python
# services/runpod-worker/worker.py
while True:
    job_data = redis_client.lpop("simhpc_jobs")
    if job_data:
        with lock:
            active_jobs += 1
        threading.Thread(target=process_job, args=(job,)).start()
```

### B. O-D-I-A-V Decision Loop Orchestration
The **Robustness Orchestrator (API)** acts as the command center, enqueuing jobs based on operator actions:
1. **Observe**: Telemetry from the Pod is pushed to Redis/Supabase.
2. **Detect**: Anomaly detection runs on the API layer.
3. **Investigate**: Historical lineage is pulled from Supabase.
4. **Act**: The operator Intercepts or Clones via the `CommandConsole`.
5. **Verify**: Final certification is written back to the DB.

---

## Repository Strategy (Security Posture)

To protect core intellectual property (AI/Physics logic) during the beta phase, the codebase is split:

- **`apps/frontend/`** (Git submodule): Contains the React/Vite application. This directory is a gitlink pointing into `lostbobo.git`. Both the submodule and the parent monorepo share the same remote (`lostbobo.git` → Vercel deployment source). Vercel auto-deploys on push to `lostbobo.git` main.
- **Parent Monorepo (`SimHPC/`)**: Contains the full platform including `robustness-orchestrator`, AI services, and physics-worker configurations. Commits to the monorepo are pushed to `lostbobo.git` main, triggering the Vercel deploy workflow and the RunPod worker deploy workflow.

---

## Project Structure

```
SimHPC/ (Monorepo — same remote as lostbobo.git)
├── apps/
│   └── frontend/                # React frontend [GIT SUBMODULE → lostbobo.git]
├── services/
│   ├── robustness-orchestrator/ # FastAPI backend [CLOSED SOURCE]
│   │   ├── api.py               # FastAPI orchestration layer
│   │   ├── robustness_service.py # Parameter sweep logic
│   │   ├── ai_report_service.py  # Mercury AI (Inception Labs) integration
│   │   ├── pdf_service.py        # Engineering PDF generation
│   │   ├── auth_utils.py          # JWT verification + Supabase auth
│   │   ├── demo_access.py         # Demo magic link system
│   │   └── requirements.txt       # Python dependencies
│   └── runpod-worker/           # GPU polling worker for RunPod
│       ├── Dockerfile            # Legacy (RunPod serverless handler)
│       ├── Dockerfile.worker     # Polling worker container (python:3.10-slim)
│       ├── worker.py             # Infinite loop polling worker
│       └── requirements.txt      # Worker dependencies
├── Dockerfile.worker            # Root-level Dockerfile for CI/CD
├── requirements.worker.txt       # Root-level requirements (redis + supabase-py)
├── supabase/
│   └── migrations/
│       └── heartbeat_history.sql # Supabase schema: worker_heartbeat,
│                                #   simulation_history, leads tables
└── .github/
    └── workflows/
        ├── deploy.yml           # Vercel deploy (amondnet/vercel-action)
        └── deploy-worker.yml    # RunPod worker deploy (v2.1.2)
```

---

## Components

### Frontend (React + Vite)
- **Framework**: React 18, TypeScript, Vite
- **Styling**: Tailwind CSS + shadcn/ui
- **Auth**: Supabase Auth (@supabase/supabase-js)
- **State**: React Context (theme, auth)
- **Charts**: Recharts for sensitivity visualization
- **State Management**: Zustand (Unified Control Room Store)
- **Animations**: Framer Motion
- **Toast Notifications**: sonner with cyan glow theme (`#00f2ff`) — `<Toaster />` mounted in `App.tsx`; toast patterns: 6s default, 8s success, 10s error
- **Real-time Updates**: `useSimulationUpdates` hook subscribes to `simulation_history` via Supabase Realtime (INSERT + UPDATE events)
- **New Components (v2.1.2)**:
  - `SimulationDetailModal` — AI insights, physics metrics, PDF download
  - `AdminAnalytics` — Active Pods, Total Jobs, Lead qualification dashboard at `/admin/analytics`
  - `toast.promise()` pattern — wraps simulation submission with loading/success/error states

### Decision Intelligence (Frontend State)
The platform uses **Zustand** (`controlRoomStore.ts`) for high-performance global state management.
- **Unified Hydration**: The `GET /api/v1/controlroom/state` aggregator populates the store on mount.
- **Event-Driven Deltas**: WebSockets specifically target store actions (`updateSimulation`, `addAlert`) to ensure 240Hz UI responsiveness.
- **Decision State Logic**: Listens for frame-accurate telemetry (`SOLVER_EVENT`), high-priority flags (`AUDIT_ALERT`), and container provisioning states.

### v2.1.2: Heartbeat Operations Center + Realtime Dashboard
- **Heartbeat Strategy**: Real-time worker health visibility via Supabase `worker_heartbeat` table.
- **Supabase Realtime**: `simulation_history` table drives live toast notifications on the frontend via `useSimulationUpdates` hook (INSERT on queue, UPDATE on running/completed/failed).
- **SimulationDetailModal**: Clickable simulation rows open a modal with AI insights, physics metrics JSON, and PDF download.
- **AdminAnalytics**: Dashboard at `/admin/analytics` showing Active Pods, Total Jobs, Lead qualification funnel.
- **TelemetryPanel**: 240Hz solver streams.
- **OperatorConsole**: High-stakes engineering actions (Intercept, Clone, Boost, Certify).
- **SimulationLineage**: Visual ancestry and Flux Delta tracking.
- **GuidanceEngine**: Mercury AI-powered strategy recommendations.

### API Orchestrator (FastAPI)
- **Server**: Uvicorn/Gunicorn
- **Auth**: JWT verification via python-jose
- **CORS**: Explicit allow-list via `ALLOWED_ORIGINS` env var (Vercel subdomains + localhost); no `allow_origins=["*"]` in production
- **Rate Limiting**: Redis-backed
- **Supabase Sync**: Inserts into `simulation_history` when a job is queued; worker updates status on completion/failure
- **Logging**: Structured JSON via structlog
- **Metrics**: Prometheus client

### Physics Worker (RunPod GPU Pods)
- **Executor**: RunPod GPU Pods (NOT Serverless)
- **GPU**: NVIDIA CUDA 12.1.0
- **Solvers**: SUNDIALS, MFEM
- **Task Queue**: Redis (list: `simhpc_jobs`)
- **Worker Type**: Infinite loop (`while True`) in `services/runpod-worker/worker.py` — NOT `runpod.serverless`
- **Concurrency**: Thread-based parallel execution with `MAX_CONCURRENT_JOBS` limit per pod
- **Supabase Sync**: Calls `update_job_status()` on running/completed/failed to sync `simulation_history` table
- **Heartbeat**: Background thread pings `worker_heartbeat` table every 30s

#### RunPod Pod Architecture (v2.1.2 - Concurrent Workers)
Clean separation between Control Plane and Compute Plane:
```
┌─────────────────────────────────────────────────────────────┐
│  CONTROL PLANE (stable, rarely changes)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │
│  │ API Server  │  │    Redis    │  │   Autoscaler    │   │
│  │  (gunicorn) │  │  (Queue)    │  │ (idle_timeout)  │   │
│  └─────────────┘  └─────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  COMPUTE PLANE (swappable, scalable)                        │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Container: simhpcworker/simhpc-worker:v2.1.2          │  │
│  │                                                         │  │
│  │  services/runpod-worker/worker.py  ←  INFINITE LOOP  │  │
│  │     │                                                 │  │
│  │     ├── Poll Redis queue (LPOP "simhpc_jobs")       │  │
│  │     ├── update_job_status() → simulation_history    │  │
│  │     ├── Thread-based parallel execution             │  │
│  │     │    (MAX_CONCURRENT_JOBS limit per pod)       │  │
│  │     └── send_heartbeat() → worker_heartbeat table   │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

```
┌─────────────────────────────────────────────────────────────┐
│  CONTROL PLANE (stable, rarely changes)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐    │
│  │ API Server  │  │    Redis    │  │   Autoscaler    │    │
│  │  (gunicorn) │  │  (Queue)    │  │ (idle_timeout)  │    │
│  └─────────────┘  └─────────────┘  └─────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  COMPUTE PLANE (swappable, scalable)                        │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Container: simhpcworker/simhpc-worker:v2.0.0         │  │
│  │                                                         │  │
│  │  worker.py  ←  INFINITE LOOP (while True)            │  │
│  │     │                                                 │  │
│  │     ├── Poll Redis queue (LPOP)                      │  │
│  │     ├── Thread-based parallel execution              │  │
│  │     │    (MAX_CONCURRENT_JOBS limit per pod)         │  │
│  │     └── Return results to Redis                      │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

```

### Worker Concurrency Model

**Per-Pod Thread Pool:**
```python
MAX_CONCURRENT_JOBS = int(os.getenv("MAX_CONCURRENT_JOBS", "2"))
active_jobs = 0
lock = threading.Lock()

while True:
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
|------|------|---------------------|----------------------|
| Small | 1 | 2 | 2 jobs |
| Medium | 2 | 2 | 4 jobs |
| Large | 3 | 2 | 6 jobs |

**Autoscaler Logic:**
1. Poll queue length every 10 seconds
2. Start pods when queue > 0
3. Stop pods after 300 seconds idle
4. Each pod maintains its own `active_jobs` counter

## Core Architecture - The O-D-I-A-V Loop (v2.1.2)

SimHPC's v2.1.0 is built around the **Operational Cockpit** concept, implementing a tight O-D-I-A-V (Observe-Detect-Investigate-Act-Verify) decision loop with a **Heartbeat Strategy** for real-time visibility:

1. **OBSERVE** → `TelemetryPanel` (240Hz solver streams & **Heartbeat Pulse** from RunPod workers)
2. **DETECT** → `AuditFeed` (Rnj-1 AI Auditor anomaly detection) 
3. **INVESTIGATE** → `SimulationMemory` (Iteration Lineage & Delta Tracking)
4. **ACT** → `OperatorConsole` (Intercept, Clone, Boost, Certify)
5. **VERIFY** → `GuidanceEngine` (Mercury AI Numerical Anchoring against solver outputs)
6. **DOCUMENT** → Physics-Verified Engineering Reports (PDF)

**Why Pods (not Serverless):**
- Serverless: Container exits after job → restart loop → wasted money
- Pods: Container runs forever → stable → predictable costs

### Persistence Layer
- **Redis**: Job states, rate limits, telemetry
- **Supabase**: User data, auth, PostgreSQL, demo_access, `worker_heartbeat`, `simulation_history`, `leads`
- **Supabase Storage**: A bucket named `results` is required for storing AI-generated PDF engineering reports.
- **S3/R2**: PDF storage (optional backup)
- **Realtime**: `simulation_history` table has Realtime enabled — INSERT/UPDATE events propagate to frontend `useSimulationUpdates` hook for live toast notifications

---

## API Endpoints

### 1. Core System APIs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/templates | Predefined simulation models |
| POST | /api/v1/simulation/estimate | Predict runtime (`≈ E * S * P`) and cost before execution |
| POST | /api/v1/solver/advisor | ML model for solver recommendation |
| GET | /api/v1/simulation/{run_id}/timeline | Physics event timeline (checks convergence/divergence) |
| POST | /api/v1/simulation/{run_id}/replay | Replay snapshot from specific timestamp |
| POST | /api/v1/simulation/guardrails | Define cost and runtime safety limits |
| POST | /api/v1/simulation/run | Trigger a template simulation |

### 2. Control Room (O-D-I-A-V Loop)
SimHPC is designed as an **Operational Cockpit** that facilitates high-stakes engineering decisions through a 6-phase cognitive loop:

1.  **Observe**: Real-time telemetry streaming (GPU load, solver convergence, residual curves).
2.  **Detect**: Rnj-1 AI Auditor flags hallucinations or discrepancies between physics and raw data.
3.  **Investigate**: Simulation Memory and Lineage Tree visualization for root-cause analysis.
4.  **Act**: Operator commands via Console (`[INTERCEPT]`, `[CLONE]`, `[BOOST]`).
5.  **Verify**: Guidance Engine validates results against RAG-anchored evidence.
6.  **Document**: Export of Physics-Verified Compliance Certificates (PDF).

#### Canonical Control Room Layout
```text
┌────────────────────────────────────────────┐
│ SimulationTimeline.tsx (top horizontal)    │
├───────────────┬────────────────────────────┤
│ Telemetry     │ ActiveCluster.tsx          │
│ Panel.tsx     │ (Running jobs)             │
│ (GPU/Solver)  │                            │
├───────────────┴────────────────────────────┤
│ SimulationMemory.tsx (Ancestry/Lineage)    │
├────────────────────────────────────────────┤
│ CommandConsole.tsx + GuidanceEngine.tsx    │
└────────────────────────────────────────────┘
```

#### O-D-I-A-V Loop Walkthrough
1.  **Observe**: Launch baseline thermal simulation and watch real-time telemetry (GPU load, solver convergence, residual curves).
2.  **Detect**: Rnj-1 AI Auditor flags any hallucinations or discrepancies between physics and raw data.
3.  **Investigate**: Use Simulation Memory and Lineage Tree visualization for root-cause analysis, comparing with historical baseline.
4.  **Act**: Execute operator commands via Console (`[INTERCEPT]`, `[CLONE]`, `[BOOST]`) to correct issues.
5.  **Verify**: Guidance Engine validates results against RAG-anchored evidence and numerical verification.
6.  **Document**: Export Physics-Verified Compliance Certificates (PDF) for audit trail.

#### System Health & Debugging
In the Alpha environment, the Control Room features a real-time `System Status` indicator on the left sidebar:
- **Mercury AI**: Verified via chat completions ping.
- **RunPod GPU**: Checked via GraphQL `myself` API.
- **Supabase DB**: Checked by establishing a query connection on `demo_access`.
- **Worker**: Checked via **Heartbeat Strategy** (Supabase `worker_heartbeat` table, pinged every 30s by `services/runpod-worker/worker.py`).
- **Simulation Status**: Frontend subscribes to `simulation_history` via Supabase Realtime — rows INSERTed when job is queued, UPDATEd when worker sets running/completed/failed.
Coupled with a *20-line Job Log Viewer*, this drastically accelerates debugging of queued runs and pod lifecycle events.

## Growth Architecture (PLG Engine)

SimHPC utilizes a Product-Led Growth (PLG) model to convert alpha pilots into enterprise contracts.

| System | Component | Purpose |
|--------|-----------|---------|
| **Acquisition** | Magic Link System | Frictionless onboarding via `/demo/:token` |
| **Engagement** | Token Metering | Usage-based compute limits (5 runs/demo) |
| **Qualification** | Lead Scoring | `POST /lead/qualify` based on demo depth |
| **Feedback** | Alpha Insights | `POST /feedback/alpha` for product iteration |
| **Monetization** | Stripe Billing | Tiered funnel: Free → Professional → Enterprise |
| **Intelligence** | Demo Analytics | `GET /analytics/demo` for conversion tracking |

#### Control Room APIs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/controlroom/state | Atomic aggregator for full cockpit hydration |
| GET | /api/v1/control/timeline | Retrieval of structured event-class logs |
| GET | /api/v1/control/lineage | Simulation ancestry data for lineage tree rendering |
| POST | /api/v1/control/command | Execution of operator overrides (intercept/clone) |
| POST | /api/v1/report/generate | Cryptographic certificate generation |
| GET | /api/v1/simulations/active | Active simulation runs (from Redis `job:*` hashes) |
| GET | /api/v1/simulations/history | Simulation history (from Redis `job:*` hashes) |

#### Event Stream Binding
- **WebSocket**: `WS /api/v1/telemetry/{run_id}`
- **Signals**: `GET /api/v1/signals/live` (1Hz heartbeat)

### 3. Commercial & Growth APIs
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/access/request | Alpha access application (lead gen) |
| POST | /api/v1/feedback/alpha | Qualitative pilot feedback (ease/value/trust) |
| GET | /api/v1/analytics/demo | Aggregated demo performance metrics |
| POST | /api/v1/lead/qualify | Automated lead scoring based on usage |

### 4. Demo Flow APIs
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/demo/start | Create a guided demo session (5 runs limit) |
| GET | /api/v1/demo/{session_id}/progress | Track progress tasks (Baseline → Parameter → Scenario → Robustness) |
| GET | /api/v1/demo/suggested-run | Rule-based next step recommendation |
| POST | /api/v1/demo/run | Run a scenario (decrements session counter) |
| POST | /api/v1/demo/complete | Finalize demo, generate report and notebook URLs |

### 4. Trust Layer APIs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/validation/benchmarks | NAFEMS error rate comparison |
| GET | /api/v1/validation/badge | Returns NAFEMS validation badge metrics |
| GET | /api/v1/simulation/{run_id}/sensitivity | Parameter impact rankings (Sobol/GSA) |
| GET | /api/v1/simulation/{run_id}/uncertainty | MC variance and 95% confidence intervals |
| GET | /api/v1/simulation/{run_id}/provenance | Full solver, hardware, and container metadata |
| POST | /api/v1/report/generate | Generate physics-verified engineering report |
| GET | /api/v1/reports/{id}/pdf | Download generated PDF export |

### 5. Authentication & Billing
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/auth/signup | User registration |
| POST | /api/v1/auth/signin | Email/magic link login |
| GET | /api/v1/auth/session | Get current session |
| POST | /api/v1/subscribe | Create Stripe checkout session |
| POST | /api/v1/billing/webhook | Handle Stripe webhooks |
| GET | /api/v1/user/profile | Get subscription status |

---

## Security Architecture

### Authentication Flow
1. User signs up/in via Supabase (Magic Link) or Google One Tap (`g_id_onload`)
   - **Google Client ID:** `552738566412-t6ba9ar8jnsk7vsd399vhh206569p61e.apps.googleusercontent.com`
2. Google GIS returns ID token -> Verified by Supabase
3. Supabase returns JWT access token -> Frontend stores in session
4. Backend verifies JWT via `python-jose`
5. **Tier Verification:** API queries Supabase `profiles` table using Service Role Key to determine `plan_id` and map to `free`/`professional`/`enterprise` tiers.
6. **Persistence:** `simulation_history` table (Supabase) receives INSERT on job queue (via `record_simulation_start()` in `api.py`) and UPDATE on completion/failure (via `update_job_status()` in `worker.py`). Realtime events propagate to frontend.

### Secrets Rotation (Production)
To maintain security across the distributed stack, the following rotation policy is enforced:
- **Supabase Service Role Key**: Rotated every 90 days via Supabase Dashboard. Requires manual update of `robustness-orchestrator` environment variables.
- **RunPod API Key**: Rotated if any breach is suspected or every 180 days. Managed via `RunPod Settings`.
- **Stripe Webhook Secret**: Rotated via Stripe Dashboard; ensures `billing/webhook` endpoint remains secure against replay attacks.
- **JWT Secret**: Managed at the root of the orchestrator; rotation triggers global session invalidation.

### Rate Limiting
- **Login/Signup**: 5 attempts/minute per IP
- **Simulations**: 10/hour per user (configurable by tier)
- **AI Reports**: 5/hour per user
- **API Keys**: Custom limits per enterprise client

### Abuse Prevention
- Google OAuth or verified email required
- Device fingerprinting (2 free accounts per device)
- IP-based limits (2 free accounts per IP)
- Free tier: 1 concurrent, 60s timeout, small mesh only
- Honeypot fields in forms
- Credit card trigger after 5 free simulations

---

## Tiered Access Model

| Feature | Free | Professional | Enterprise | Demo (Gen) | Demo (Full) | Demo (Magic) |
|---------|------|--------------|------------|------------|-------------|-------------|
| Simulation runs | 5 max | 50 | Unlimited | 10 | 100 | 5 (configurable) |
| Perturbation runs | 5 | 50 | Unlimited | 5 | 100 | 5 |
| AI reports | - | ✓ | ✓ | ✓ | ✓ | ✓ |
| PDF export | - | ✓ | ✓ | - | ✓ | - |
| Cached reports | - | ✓ | ✓ | ✓ | ✓ | ✓ |
| API access | - | - | ✓ | - | ✓ | - |
| Custom sampling | - | - | ✓ | - | ✓ | - |
| Sobol GSA | - | - | ✓ | ✓ | ✓ | - |
| Priority queue | - | - | ✓ | - | ✓ | - |
| High-res grids | 5k nodes | 50k nodes | Unlimited | 5k nodes | 50k nodes | 5k nodes |
| Experiment Trees | - | ✓ | ✓ | - | ✓ | - |
| Advanced Lineage | - | ✓ | ✓ | - | ✓ | - |
| Auto-expiry | - | - | - | 60 min | 60 min | 7 days |

---

## Free Tier Enforcement Layer (v1.6.0-ALPHA)

### 1. Database & Usage Enforcement (Supabase)

**Rolling 7-Day Window:**
- **Allowance:** 5 simulations per 7-day rolling window
- **Reset Logic:** Uses `reset_timestamp`. If `current_time > reset_timestamp`, resets `runs_used` to 0
- **Concurrency:** Blocks new job submission if `status == 'running'` for the current user

**Implementation:**
```python
# In api.py
async def get_user_usage(user_id: str) -> dict:
    """Get current usage stats for a user with rolling 7-day window."""
    
async def increment_user_usage(user_id: str, runs: int = 1) -> bool:
    """Increment user usage count within rolling window."""
    
async def check_concurrent_runs(user_id: str) -> bool:
    """Check if user has any running simulations."""
```

### 2. Compute & Physics Guards (RunPod Pods/MFEM)

**Hard Limits on Simulation Payload:**
- **Grid Resolution Cap:** Reject any simulation configuration exceeding **5,000 nodes** for free tier
- **Runtime Timeout:** Jobs have 30-minute limit (configurable via `JOB_TIMEOUT_SEC` env var)
- **Scenario Gating:** Only allow `baseline`, `stress`, and `extreme` presets. Return `403 Forbidden` for `custom_scenarios`
- **Idle Shutdown:** Autoscaler stops pods after 10 minutes of queue emptiness

**Implementation:**
```python
# In PLAN_LIMITS
UserPlan.FREE: {
    "max_grid_nodes": 5000,
    "allowed_scenarios": ["baseline", "stress", "extreme"]
}
```

### 3. Module & Memory Restrictions

**Free Tier Restrictions:**
- **Single Module Only:** Enforce a check that only one module (Fire, Battery, or Grid) is active per run
- **Memory Access:** Disable the `SimulationLineage` and `SimulationMemory` components for users with `tier == 'free'`
- **Retention:** Add a "Simulations expire in 24h" warning to the results UI

### 4. Frontend UX & Upgrade Triggers

**Dashboard Updates:**
- **Status Indicators:** Add a "Runs Remaining: X/5" counter in the left sidebar (SystemStatus component)
- **Feature Gating:** Greyscale/Lock icons for: API Access, Data Upload, Experiment Trees, and Advanced Visualizations
- **Upgrade Toasts:** Trigger a 'Premium Feature' modal when a free user clicks a locked feature or hits their 5-run limit

**Message Template:**
> "You've reached your weekly limit. Upgrade to Pro for unlimited runs, high-res grids (100k+ nodes), and API access."

### 5. API Endpoints

**Tier Enforcement Middleware:**
- `check_plan_limits()` - Enforces run limits and feature availability
- `check_concurrent_runs()` - Prevents multiple simultaneous runs for free tier
- Usage tracking integrated into `start_robustness()` endpoint

**Error Responses:**
```json
{
  "message": "You've reached your weekly limit. Upgrade to Pro for unlimited runs, high-res grids (100k+ nodes), and API access.",
  "plan": "free",
  "used": 3,
  "limit": 5,
  "requested": 2,
  "remaining": 2
}
```

---

## System Hardening & Security Architecture (v1.6.0-ALPHA)

### 1. Authentication & JWT Security (`auth_utils.py`)

**Eliminated Placeholders:**
- Removed insecure fallback for `SUPABASE_JWT_SECRET`
- System now raises `RuntimeError` at startup if environment variable is missing

**Clock Skew & Validation:**
```python
payload = jwt.decode(
    token, 
    SUPABASE_JWT_SECRET, 
    algorithms=["HS256"], 
    audience=SUPABASE_AUDIENCE,
    options={
        "verify_exp": True,
        "verify_nbf": True,
        "verify_iat": True,
        "verify_aud": True,
        "verify_iss": False,
        "require_exp": True,
        "require_iat": True,
    },
    leeway=30  # 30-second clock skew tolerance
)
```

**Audience Isolation:**
- Configurable via `SUPABASE_AUDIENCE` env var
- Defaults to `authenticated` for development environments

### 2. Persistence & Cache Strategy

**Primary Source of Truth:**
- Supabase established as the Primary Truth for all data

**Write-Through Cache Pattern:**
- "Supabase-First" write strategy for `demo_access` and `simulation_jobs`
- Redis used as write-through cache with 60-second TTL
- Prevents stale data and cache inconsistency

**Token Revocation:**
- `denylist` implemented in Redis for immediate token revocation
- Supports Magic Link token invalidation

### 3. Endpoint Protection & User Isolation

**Real User Verification:**
```python
async def get_current_user(authorization: str = Header(None)):
    """
    Strict authentication dependency for protected endpoints.
    Only accepts Supabase JWT tokens - no API key or anonymous access.
    """
    if not authorization:
        raise HTTPException(401, "Missing token")
    return verify_user(authorization)  # Can raise 401
```

**Standardized Naming:**
- Administrative endpoints use `X-Admin-Secret` header
- Removed fallback where `ADMIN_SECRET` defaults to `SIMHPC_API_KEY`

### 4. Scientific Soundness & PDF Safety

**Numerical Anchoring Regex:**
```python
DANGEROUS_PATTERNS = [
    (r"(will|shall|definitely|guaranteed).*fail", "may fail"),
    (r"(certain|sure|undoubtedly).*safe", "appears safe"),
    (r"material (will|can) (break|fracture|yield)", "material may experience stress"),
]
```

**Font Fallback Logic:**
```python
def get_font_path(filename: str) -> Optional[Path]:
    """
    Returns Path object if font found, None if not found.
    """
    # ... search logic ...
    return None  # If not found

# In SimHPCPDFReport.__init__:
font_path = get_font_path("DejaVuSans.ttf")
if font_path:
    self.add_font('DejaVu', '', str(font_path), uni=True)
    # ... load other variants ...
else:
    logger.warning("Using built-in Helvetica – limited Unicode support")
```

### 5. Robustness & Degradation

**Silent Failure Prevention:**
- Removed mock for `SobolAnalyzer`
- If module is missing, system must log `CRITICAL` error and return "Service Unavailable"
- No fallback implementation that could mask deployment issues

### 6. Secure Endpoint Examples

**Protected Endpoint Usage:**
```python
@app.post("/api/v1/robustness/run", response_model=JobResponse, tags=["Simulations"])
async def start_robustness(
    request: RobustnessRunRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),  # Strict JWT only
    x_idempotency_key: str = Header(None),
):
    # ... implementation uses current_user instead of verify_auth ...
```

---

## Heartbeat Strategy (v2.1.0)

### Overview
To ensure real-time visibility into the distributed GPU Pod cluster, SimHPC implements a **Heartbeat Strategy**. The worker process sends periodic health signals to Supabase, allowing the Mission Control frontend to toggle the UI LED based on the freshness of the heartbeat.

### Backend Implementation (`services/runpod-worker/worker.py`)
The worker sends heartbeats to Supabase `worker_heartbeat` table via a background thread.

```python
def send_heartbeat():
    """Send heartbeat to Supabase."""
    if not supabase:
        return
    try:
        supabase.table("worker_heartbeat").upsert(
            {
                "worker_id": RUNPOD_POD_ID,
                "status": "online",
                "last_ping": datetime.utcnow().isoformat(),
            }
        ).execute()
    except Exception as e:
        logger.error(f"Heartbeat failed: {e}")
```

### API Implementation (`api.py`)
The orchestrator provides a lightweight endpoint for the frontend to verify system health.

```python
@app.get("/api/v1/system/status")
async def get_worker_status():
    """Returns the health status of the GPU Pod cluster."""
    # Fetches latest heartbeat from supabase worker_heartbeat table
    # Returns "online" if last_ping < 90 seconds, else "stalled"
```

### Key Features:
- **Zero-Cost Polling**: Frontend checks Supabase instead of triggering RunPod API calls.
- **Persistence**: Heartbeat logs provide a historical record of worker uptime.
- **Scalability**: Supports multiple workers by using `worker_id` as the primary key.

### Frontend Implementation (`SystemStatus.tsx`)

**Status LED Component:**
```typescript
const StatusLED = ({ state }: { state: string }) => {
  const isGood = ['online', 'connected', 'warm'].includes(state);
  return (
    <div className="flex items-center space-x-2 my-1">
      <div className={`h-2.5 w-2.5 rounded-full ${isGood ? 'bg-green-500 shadow-[0_0_8px_#22c55e]' : 'bg-red-500'} ${isGood && 'animate-pulse'}`} />
      <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
        {state || 'checking...'}
      </span>
    </div>
  );
};
```

**Polling Interval:**
- Status checks every **30 seconds** to maintain lean operation
- Real-time feedback on service health without overloading the system

### RunPod Worker (`services/runpod-worker/worker.py`)

**Pod Worker - Infinite Loop:**
```python
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_NAME = os.getenv("QUEUE_NAME", "simhpc_jobs")
RUNPOD_POD_ID = os.getenv("RUNPOD_POD_ID", f"worker-{os.getpid()}")

def update_job_status(job_id: str, status: str, result: dict = None):
    """Sync simulation status to Supabase simulation_history table."""
    if not supabase:
        return
    data = {"status": status}
    if result:
        data["result_summary"] = result
        data["report_url"] = result.get("pdf_link")
    supabase.table("simulation_history").update(data).eq("job_id", job_id).execute()

def process_job(job: dict):
    job_id = job.get("id", "unknown")
    update_job_status(job_id, "running")
    # ... run simulation ...
    update_job_status(job_id, "completed", result)
    update_job_status(job_id, "failed", {"error": str(e)})

def main():
    while True:
        job_data = redis_client.lpop("simhpc_jobs")
        if job_data:
            job = json.loads(job_data)
            with lock:
                active_jobs += 1
            threading.Thread(target=process_job, args=(job,)).start()
            send_heartbeat()
        else:
            time.sleep(POLL_INTERVAL_SEC)
```

**Key Differences from Serverless:**
| Aspect | Serverless | Polling Pod (Current) |
|--------|-----------|-----------------------|
| Container Lifecycle | Exits after job | Runs forever |
| Job Polling | RunPod event | Redis LPOP |
| Status Sync | N/A | Supabase `simulation_history` INSERT/UPDATE |
| Cost Model | Per-job + cold starts | Predictable hourly |
| Health Check | HTTP endpoint | `while True:` + heartbeat thread |

### O-D-I-A-V Loop Integration

This implementation fulfills the **Observe** and **Detect** stages:

1. **Observe:** Real-time status LEDs show service health (Mercury, Worker, Supabase)
2. **Detect:** Instant feedback if the "Trust Layer" (Mercury) or "Action Layer" (RunPod) is compromised

### Cost Control Benefits

- **Predictable Costs:** Pods charge by the hour, not per job
- **No Cold Starts:** Worker stays warm in memory
- **Idle Auto-shutdown:** Autoscaler stops pods when queue is empty
- **Lean Operation:** 2-second polling interval prevents unnecessary load

## Deployment

### Production Stack
- **Frontend**: Vercel (via `lostbobo` repo at https://github.com/NexusBayArea/lostbobo.git)
- **Production URL**: https://simhpc.com
- **Backend API**: `simhpc/api:alpha` container on RunPod
- **GPU Worker**: `simhpcworker/simhpc-worker:v2` pods on RunPod
- **Autoscaler**: `simhpc/autoscaler:alpha` monitors queue and manages pods
- **Database**: Supabase PostgreSQL (No Git sync)
- **Cache/Queue**: Redis 7 (alpine)

### Docker Images
| Image | Purpose | Base Image |
| :--- | :--- | :--- |
| `simhpc/api:alpha` | FastAPI backend | `python:3.11-slim` |
| `simhpcworker/simhpc-worker:v2.1.2` | GPU polling worker | `python:3.10-slim` |
| `simhpc/autoscaler:alpha` | Queue monitoring | `python:3.11-slim` |
| `lostbobo/lostbobo:latest` | Frontend (Vercel build output) | N/A |

### Environment Variables
```bash
# Supabase
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_JWT_SECRET=

# API
SIMHPC_API_KEY=
REDIS_URL=redis://redis:6379/0
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,https://*.vercel.app

# AI
MERCURY_API_KEY=
MERCURY_MODEL=mercury-2

# Billing
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRO_PRICE_ID=

# Security
AUTH_SECRET=
GOOGLE_CLIENT_ID=552738566412-t6ba9ar8jnsk7vsd399vhh206569p61e.apps.googleusercontent.com

# RunPod Pod Worker (GPU)
REDIS_URL=redis://your-redis-host:6379/0
POLL_INTERVAL_SEC=2
IDLE_TIMEOUT=300
MAX_CONCURRENT_JOBS=2
SUPABASE_URL=           # For update_job_status() sync
SUPABASE_SERVICE_ROLE_KEY=
```

---

## Key Services

### RobustnessService
- Handles parameter sampling (±5%, ±10%, Latin Hypercube, Monte Carlo, Sobol)
- Manages baseline caching to prevent redundant GPU computation
- Implements input validation with physical parameter bounds
- Caps concurrent jobs (max 8) to prevent GPU exhaustion

### AIReportService
- Mercury AI (Inception Labs) integration for interpretive reports.
- **Role in Alpha**: 
  1. **Simulation Setup Assistance**: Interprets natural language inputs into structured simulation parameters.
  2. **Notebook Generation**: Generates explanatory text and engineering summaries based on solver outputs.
- **Constraints**: 
  - Advisory only; never used for core physics, experiment selection, or validation.
  - Scientific tone enforcement (100-1000 chars, keyword constraints).
  - 24-hour TTL cache for technical interpretations.
  - Numerical anchor verification (The Anchor) against raw simulation metrics.

### PDFService
- FPDF-based PDF generation
- Matplotlib charts for sensitivity rankings
- DejaVu fonts with Helvetica fallback
- S3/R2 upload with signed URLs

---

## Appendix: Mercury AI Usage in Alpha

### 1. Where Mercury Is Used in Alpha

In your current Alpha architecture, **Mercury should only be used in two places**:

#### 1️⃣ Simulation Setup Assistance

Mercury helps interpret user inputs into simulation parameters.

Example:

User input:
```
simulate high temperature stress
```

Mercury converts it into structured parameters:
```
temperature: 45
duration: 48h
wind: moderate
```

Then the simulation module runs.

So the flow is:
```
User Input
↓
Mercury interpretation
↓
Simulation parameters
↓
RunPod simulation
```

#### 2️⃣ Notebook Generation

Mercury writes the **explanatory text** inside the notebook.

Example:

Simulation output:
```
voltage_drop = 8%
temperature = 42C
```

Mercury generates:
```
The simulation indicates that elevated temperatures resulted in an 8% voltage drop,
suggesting increased thermal stress on the battery system.
```

So the flow is:
```
Simulation results
↓
Mercury explanation
↓
Notebook summary
```

### 2. Where Mercury Should NOT Be Used in Alpha

Avoid using Mercury for:

❌ actual physics simulations
❌ experiment selection
❌ simulation validation

### 3. Simple Mercury Health Test

The easiest test is to create a **test endpoint**.

Example:

Node.js example:
```javascript
export async function testMercury(req, res) {
  const response = await fetch("https://api.inceptionlabs.ai/v1/chat/completions", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${process.env.MERCURY_API_KEY}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      model: "mercury",
      messages: [
        { role: "user", content: "Return the word SIMHPC_OK" }
      ]
    })
  });

  const data = await response.json();
  res.json(data);
}
```

Expected response:
```
SIMHPC_OK
```

If you get that, Mercury is working.

### 4. Test From Terminal

You can test Mercury directly with curl:
```
curl https://api.inceptionlabs.ai/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mercury",
    "messages": [
      {"role":"user","content":"reply SIMHPC_OK"}
    ]
  }'
```

Expected output:
```
SIMHPC_OK
```

### 5. What Alpha Mercury Usage Should Look Like

Ideal Alpha flow:
```
User runs simulation
↓
RunPod executes model
↓
Results returned
↓
Mercury writes explanation
↓
Notebook generated
```

So Mercury is **assistive**, not core.

### 6. Quick Mercury Test Inside Your System

The fastest test you can run right now:

Add this temporary call inside notebook generation:

Prompt:
```
Explain the following simulation result in one sentence.
```

If the notebook text appears → **Mercury is working**.