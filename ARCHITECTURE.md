# SimHPC Architecture

> Last Updated: March 25, 2026
> Status: **LIVE (v2.2.0)**

---

## System Overview

SimHPC is a cloud-native GPU-accelerated finite element simulation platform. The architecture follows a distributed microservices pattern with a **securely isolated frontend** and a **closed-source backend** orchestration layer.

### The "Mission Control" Stack (v2.2.0)

For local development and alpha testing, the platform uses a unified `docker-compose.yml` stack:

- **Redis (Broker)**: `redis:7-alpine` — Handles job queueing and inter-service messaging.
- **Orchestrator (API)**: `Dockerfile.api` — FastAPI-based control plane for AI and fleet management.
- **Physics Engine (Worker)**: `Dockerfile.worker` — NVIDIA CUDA 12.1 based worker with full physics stack.

---

## 1. The Physics Worker: Dedicated Pod Architecture (v2.2.0)

Unlike the initial pod SimHPC_P_01 prototype, the SimHPC Physics Worker runs as a **long-lived stateful pod** to ensure deterministic physics results and low-latency telemetry.

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

```text
SimHPC/ (Monorepo — same remote as lostbobo.git)
├── apps/
├── services/
├── robustness-orchestrator/ # FastAPI backend [CLOSED SOURCE]
│   ├── api.py               # FastAPI orchestration layer
│   ├── robustness_service.py # Parameter sweep logic
│   ├── ai_report_service.py  # Mercury AI (Inception Labs) integration
│   ├── pdf_service.py        # Engineering PDF generation
│   ├── auth_utils.py          # JWT verification + Supabase auth
│   ├── demo_access.py         # Demo magic link system
│   └── requirements.txt       # Python dependencies
├── runpod-worker/           # GPU polling worker for RunPod
│   ├── Dockerfile            # Legacy (pod SimHPC_P_01)
│   ├── Dockerfile.worker     # Polling worker container (python:3.10-slim)
│   ├── worker.py             # Infinite loop polling worker
│   └── requirements.txt      # Worker dependencies
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

- **Framework**: React 18, TypeScript, Vite.
- **Styling**: Tailwind CSS + shadcn/ui.
- **Auth**: Supabase Auth (@supabase/supabase-js).
- **State Management**: Zustand (Unified Control Room Store).
- **Toast Notifications**: sonner with cyan glow theme (`#00f2ff`) — `<Toaster />` mounted in `App.tsx`.
- **Real-time Updates**: `useSimulationUpdates` hook subscribes to `simulation_history` via Supabase Realtime.

### Decision Intelligence (Frontend State)

The platform uses **Zustand** (`controlRoomStore.ts`) for high-performance global state management.

- **Unified Hydration**: The `GET /api/v1/controlroom/state` aggregator populates the store on mount.
- **Event-Driven Deltas**: WebSockets (via Realtime) specifically target store actions ensure 240Hz UI responsiveness.
- **Decision State Logic**: Listens for frame-accurate telemetry (`SOLVER_EVENT`), high-priority flags (`AUDIT_ALERT`), and container provisioning states.

### v2.1.2: Heartbeat Operations Center + Realtime Dashboard

- **Heartbeat Strategy**: Real-time worker health visibility via Supabase `worker_heartbeat` table.
- **Supabase Realtime**: `simulation_history` table drives live toast notifications on the frontend via `useSimulationUpdates` hook.
- **SimulationDetailModal**: Clickable simulation rows open a modal with AI insights, physics metrics JSON, and PDF download.
- **AdminAnalytics**: Dashboard at `/admin/analytics` showing Active Pods, Total Jobs, Lead qualification funnel.
- **OperatorConsole**: High-stakes engineering actions (Intercept, Clone, Boost, Certify).

### API Orchestrator (FastAPI)

- **Server**: Uvicorn/Gunicorn.
- **Auth**: JWT verification via python-jose.
- **CORS**: Explicit allow-list via `ALLOWED_ORIGINS` env var; no `allow_origins=["*"]` in production.
- **Supabase Sync**: Inserts into `simulation_history` when a job is queued; worker updates status on completion/failure.

### Physics Worker (RunPod GPU Pods)

- **Executor**: RunPod GPU Pods (e.g., NVIDIA A40).
- **Solvers**: SUNDIALS, MFEM.
- **Task Queue**: Redis (list: `simhpc_jobs`).
- **Worker Type**: Infinite loop (`while True`) in `services/runpod-worker/worker.py`.
- **Heartbeat**: Background thread pings `worker_heartbeat` table every 30s.

### Supabase Sync & Report Storage

The worker maintains a real-time connection to Supabase to synchronize simulation state and store artifacts:

- **Status Sync**: Calls `update_job_status()` on `running`, `completed`, and `failed` events.
- **Report Generation**: Upon completion, the worker generates a professional engineering PDF report using `fpdf2`.
- **Artifact Storage**: Reports are uploaded to the `reports` bucket in Supabase Storage.
- **Access Control**:
  - **Free/Demo Users**: Receive a **Public URL** for the report.
  - **Paid Users**: Receive a **Signed URL** (1-hour expiration) for enhanced security.

#### RunPod Pod Architecture (v2.1.2 - Concurrent Workers)

Clean separation between Control Plane and Compute Plane:

```text
┌─────────────────────────────────────────────────────────────┐
│  CONTROL PLANE (stable, rarely changes)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐      │
│  │ API Server  │  │    Redis    │  │   Autoscaler    │      │
│  │  (gunicorn) │  │  (Queue)    │  │ (idle_timeout)  │      │
│  └─────────────┘  └─────────────┘  └─────────────────┘      │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  COMPUTE PLANE (swappable, scalable)                        │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Container: simhpcworker/simhpc-worker:v2.1.2        │    │
│  │                                                       │    │
│  │  services/runpod-worker/worker.py  ←  INFINITE LOOP   │    │
│  │     │                                                 │    │
│  │     ├── Poll Redis queue (LPOP "simhpc_jobs")         │    │
│  │     ├── update_job_status() → simulation_history      │    │
│  │     ├── Thread-based parallel execution               │    │
│  │     │    (MAX_CONCURRENT_JOBS limit per pod)         │    │
│  │     └── send_heartbeat() → worker_heartbeat table     │    │
│  └─────────────────────────────────────────────────────┘    │
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
| :--- | :--- | :--- | :--- |
| Small | 1 | 2 | 2 jobs |
| Medium | 2 | 2 | 4 jobs |
| Large | 3 | 2 | 6 jobs |

**Autoscaler Logic (v2.2.1 — Queue-Aware Multi-Pod):**

1. Poll queue length (`pending`) and `simhpc_inflight` every `POLL_INTERVAL` seconds.
2. Scale up: `needed = min(MAX_PODS, ceil((pending + inflight) / MAX_JOBS_PER_GPU))`.
3. **GPU Selection**: Automated preference for cost-efficient A40 GPUs with RTX 3090 fallback.
4. Scale down: Individual pods are stopped after `IDLE_TIMEOUT` (300s) of inactivity.
5. **Activity Tracking**: Workers update `pods:last_used:{id}` in Redis after every job and poll cycle.
6. State persisted to Redis (`pods:active` set) + synced against RunPod API each cycle.

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
| `/api/v1/admin/fleet` | GET | Fleet status dashboard data |
| `/api/v1/admin/fleet/cost` | GET | Cost tracking summary |
| `/api/v1/admin/fleet/pod/{id}/stop` | POST | Stop pod |
| `/api/v1/admin/fleet/pod/{id}/terminate` | POST | Terminate pod |

---

## Core Architecture - The O-D-I-A-V Loop (v2.1.2)

SimHPC is built around the **Operational Cockpit** concept, implementing a tight O-D-I-A-V (Observe-Detect-Investigate-Act-Verify) decision loop:

1. **OBSERVE** → `TelemetryPanel` (240Hz solver streams & **Heartbeat Pulse** from RunPod workers).
2. **DETECT** → `AuditFeed` (Rnj-1 AI Auditor anomaly detection).
3. **INVESTIGATE** → `SimulationMemory` (Iteration Lineage & Delta Tracking).
4. **ACT** → `OperatorConsole` (Intercept, Clone, Boost, Certify).
5. **VERIFY** → `GuidanceEngine` (Mercury AI Numerical Anchoring).
6. **DOCUMENT** → Physics-Verified Engineering Reports (PDF).

### Persistence Layer

- **Redis**: Job states, rate limits, telemetry.
- **Supabase**: User data, auth, PostgreSQL, `worker_heartbeat`, `simulation_history`.
- **Supabase Storage**: Bucket named `reports` for storing engineering PDF reports.
- **Realtime**: `simulation_history` table allows live toast notifications via `useSimulationUpdates`.

---

## O-D-I-A-V Loop Walkthrough

SimHPC is designed as an **Operational Cockpit** that facilitates high-stakes engineering decisions through a 6-phase cognitive loop:

1. Observe: Launch baseline thermal simulation and watch real-time telemetry.
2. Detect: Rnj-1 AI Auditor flags any hallucinations or discrepancies.
3. Investigate: Use Simulation Memory and Lineage Tree visualization for root-cause analysis.
4. Act: Execute operator commands via Console (`[INTERCEPT]`, `[CLONE]`, `[BOOST]`).
5. Verify: Guidance Engine validates results against RAG-anchored evidence.
6. Document: Export Physics-Verified Compliance Certificates (PDF) for audit trail.

### System Health & Debugging (v2.2.0)

In the Alpha environment, the Control Room features a real-time `System Status` indicator powered by the **Aggregated Health API (`GET /api/v1/system/status`)**:

- **Mercury AI**: Verified via active chat completions ping to `mercury-2`.
- **RunPod GPU**: Checked via real-time Redis connectivity status.
- **Supabase**: Verified via active client initialization check.
- **Worker**: Checked via **Heartbeat Strategy** (Supabase `worker_heartbeat` table, pinged every 30s by active workers).
- **Security Guard**: API includes a production check that blocks `localhost` Redis usage when running on Vercel to prevent "Offline" blips.

---

## Security & Environment Policy (v2.2.1)

#### 1. The "Double-Key" Strategy
To balance user security with high-performance worker throughput, SimHPC employs a split Supabase key architecture:
- **Client Plane (Frontend)**: Utilizes `VITE_SUPABASE_ANON_KEY`. Restricted by Row Level Security (RLS) to ensure users can only access their own simulations and profile data.
- **Compute Plane (Worker)**: Utilizes `SUPABASE_SERVICE_ROLE_KEY`. Bypasses RLS to allow the worker to update simulation statuses, upload PDFs, and record heartbeats without per-request user authentication overhead.

#### 2. Stable Connectivity (RunPod Proxy)
The production environment uses the **RunPod HTTP Proxy** (mapped to Port 8000 by default) for all API communications.
- **Stable URLs**: `https://x613fv0zoyvtx9-8000.proxy.runpod.net` provides a static endpoint that persists across pod restarts.
- **Direct Access**: `194.68.245.30:22128` (TCP port mapping for SSH/Direct access).
- **SSH**: `ssh root@194.68.245.30 -p 22128 -i ~/.ssh/id_ed25519`
- **CORS Hardening**: The API orchestrator explicitly allows requests from `simhpc.com` and Vercel preview domains. The wildcard origin `*` is strictly prohibited in production.

### Authentication Flow

1. User signs up/in via Supabase (Magic Link) or Google One Tap.
   - **Google Client ID:** `552738566412-t6ba9ar8jnsk7vsd399vhh206569p61e.apps.googleusercontent.com`
2. Backend verifies JWT via `python-jose`.
3. **Tier Verification:** API queries Supabase `profiles` table to determine `plan_id`.
4. **Persistence:** `simulation_history` table (Supabase) receives status updates from workers.

### Connectivity & CORS
- **Allowed Origins**: Hardened to `simhpc.nexusbayarea.com`, `simhpc.com`, and Vercel preview branches.
- **Environment Sync**: Critical keys (`REDIS_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SIMHPC_API_KEY`) must be synchronized between Vercel and RunPod for full system availability.

### Rate Limiting

- **Login/Signup**: 5 attempts/minute per IP.
- **Simulations**: 10/hour per user (configurable by tier).
- **Free Tier**: 1 concurrent, 60s timeout, small mesh only.

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
- Handles parameter sampling (±5%, ±10%, Latin Hypercube, Monte Carlo, Sobol).
- Manages baseline caching and input validation.
- Caps concurrent jobs to prevent GPU exhaustion.

### AIReportService
- Mercury AI (Inception Labs) integration for interpretive reports.
- **Role**: Interprets natural language inputs and generates explanatory notebook text.
- **Constraints**: 24-hour TTL cache, scientific tone enforcement.

### PDFService
- FPDF-based PDF generation.
- Matplotlib charts for sensitivity rankings.
- Artifact storage in Supabase Storage with signed URL access.

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