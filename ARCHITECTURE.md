# SimHPC Architecture

> Last Updated: March 10, 2026

---

## System Overview

SimHPC is a cloud-native GPU-accelerated finite element simulation platform. The architecture follows a distributed microservices pattern with a **securely isolated frontend** and a **closed-source backend** orchestration layer.

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   Vercel        │       │   RunPod        │       │   Supabase      │
│ (Frontend Only) │──────▶│ (API + Worker)  │──────▶│ (Auth + DB)     │
│ React + Vite    │       │ FastAPI + Celery│       │ PostgreSQL      │
│ [Public/Private]│       │ Redis + GPU     │       │ [No Git Sync]   │
└─────────────────┘       │ [Closed Source] │       └─────────────────┘
         │                └─────────────────┘                ▲
         │                         ▲                         │
         └─────────────────────────┼─────────────────────────┘
                                   │
                          JWT Auth (python-jose)
```

---

## Repository Strategy (Security Posture)

To protect core intellectual property (AI/Physics logic) during the beta phase, the codebase is split:

- **`simhpc-frontend`**: Contains *only* the React/Vite application. This repository is connected to Vercel for automated deployments.
- **Monorepo (Private)**: Contains the full platform, including the `robustness-orchestrator`, AI services, and physics-worker configurations. This remains closed-source and is never linked to Vercel or Supabase.

---

## Project Structure

```
SimHPC/ (Private Monorepo)
├── apps/
│   └── frontend/                # React frontend source [CANONICAL]
├── archive/
│   └── saas-starter/            # Deprecated Next.js SaaS starter template
├── services/
│   ├── robustness-orchestrator/ # Python backend services [CLOSED SOURCE]
│   │   ├── api.py               # FastAPI orchestration layer
│   │   ├── robustness_service.py # Parameter sweep logic
│   │   ├── ai_report_service.py  # Mercury AI (Inception Labs) integration
│   │   └── pdf_service.py        # Engineering PDF generation
│   └── runpod-worker/           # GPU-enabled worker for RunPod
├── packages/
│   └── sdk/                     # SimHPC Python SDK
└── docs/                        # Project documentation
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

### Decision Intelligence (Frontend State)
The platform uses **Zustand** (`controlRoomStore.ts`) for high-performance global state management.
- **Unified Hydration**: The `GET /api/v1/controlroom/state` aggregator populates the store on mount.
- **Event-Driven Deltas**: WebSockets specifically target store actions (`updateSimulation`, `addAlert`) to ensure 240Hz UI responsiveness.
- **Decision State Logic**: Listens for frame-accurate telemetry (`SOLVER_EVENT`), high-priority flags (`AUDIT_ALERT`), and container provisioning states.

### API Orchestrator (FastAPI)
- **Server**: Uvicorn/Gunicorn
- **Auth**: JWT verification via python-jose
- **Rate Limiting**: Redis-backed
- **Logging**: Structured JSON via structlog
- **Metrics**: Prometheus client

### Physics Worker (Celery / RunPod Serverless)
- **Executor**: Celery with Redis broker or RunPod Serverless Endpoint
- **GPU**: NVIDIA CUDA 12.2.0
- **Solvers**: SUNDIALS, MFEM
- **Task Queue**: Supabase / Redis

#### RunPod Job Dispatcher Architecture
To prevent the #1 serverless failure (GPU cold start overload, job loss, timeouts due to direct user-to-worker requests), SimHPC uses an **API Job Dispatcher layer**:
```
User -> Frontend -> API Job Dispatcher -> Supabase Job Queue -> RunPod Worker -> Results stored
```
**Job Flow:**
1. **User submits simulation** -> Backend inserts job into `simulation_jobs` table (status = queued).
2. **Dispatcher sends job** -> Backend pulls queued job and sends to RunPod endpoint via API.
3. **Worker runs simulation** -> Serverless handler executes physics model.
4. **Store result** -> Job marked as completed and results stored securely in Supabase.

### Persistence Layer
- **Redis**: Job states, rate limits, telemetry
- **Supabase**: User data, auth, PostgreSQL, demo_access
- **Supabase Storage**: A bucket named `results` is required for storing AI-generated PDF engineering reports.
- **S3/R2**: PDF storage (optional backup)

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
- **Worker**: Checked via RunPod endpoint health status.
Coupled with a *20-line Job Log Viewer*, this drastically accelerates debugging of serverless timeouts and queued runs.

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
3. Supabase returns JWT access token
3. Frontend stores token in session
4. Backend verifies JWT via `python-jose`
5. **Tier Verification:** API queries Supabase `profiles` table using Service Role Key to determine `plan_id` and map to `free`/`professional`/`enterprise` tiers.
6. **Persistence:** Final physics data and simulation summaries are inserted into the `simulations` or `simulation_history` table in Supabase.

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

### 2. Compute & Physics Guards (RunPod/MFEM)

**Hard Limits on Simulation Payload:**
- **Grid Resolution Cap:** Reject any simulation configuration exceeding **5,000 nodes** for free tier
- **Runtime Timeout:** Set a hard `30s` GPU execution limit in the RunPod `runsync` call
- **Scenario Gating:** Only allow `baseline`, `stress`, and `extreme` presets. Return `403 Forbidden` for `custom_scenarios`

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

## Metadata-Only Worker Ping (v1.6.0-ALPHA)

### Overview
To keep v1.6.0-ALPHA running lean and avoid unnecessary GPU costs, we implemented a **"Metadata-Only" ping** for the Simulation Worker. This confirms the worker is "Warm" and the API is reachable without triggering a full 412.3K thermal simulation.

### Backend Implementation (`api.py`)

**System Status Endpoint:**
```python
@app.get("/api/v1/system-status")
async def get_system_status():
    """
    Checks Mercury AI, Supabase, and Simulation Worker status.
    Uses metadata-only ping for worker to avoid GPU costs.
    """
    # 1. Mercury Check (Inception Labs)
    # 2. Supabase Check
    # 3. Simulation Worker Check (RunPod Serverless - Metadata Only)
    #    Sends {"input": {"check_health_only": True}} to bypass physics
```

**Key Features:**
- **Parallel Checks:** All services checked concurrently with 2-second timeout
- **Metadata-Only Worker Ping:** Sends `check_health_only: True` flag to RunPod endpoint
- **Cost Control:** Worker responds immediately without spinning up GPU kernels

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

### RunPod Worker Handler (`main.py`)

**Health Check Guard:**
```python
@app.post("/runsync", dependencies=[Depends(get_api_key)])
async def runsync(input_data: dict):
    """
    RunPod runsync endpoint handler.
    Supports metadata-only health check to avoid GPU costs.
    """
    inputs = input_data.get("input", {})
    
    # NEW: Alpha Health Check Guard (Metadata-Only Ping)
    if inputs.get("check_health_only"):
        return {"status": "ready", "worker_id": os.environ.get("RUNPOD_POD_ID", "unknown")}
    
    # Existing simulation logic would go here
    return {
        "status": "complete",
        "result": "Simulation placeholder",
        "worker_id": os.environ.get("RUNPOD_POD_ID", "unknown")
    }
```

### O-D-I-A-V Loop Integration

This implementation fulfills the **Observe** and **Detect** stages:

1. **Observe:** Real-time status LEDs show service health (Mercury, Worker, Supabase)
2. **Detect:** Instant feedback if the "Trust Layer" (Mercury) or "Action Layer" (RunPod) is compromised

### Cost Control Benefits

- **No GPU Spin-up:** Health checks return immediately without loading models
- **Minimal Network Traffic:** Small JSON payload vs. full simulation data
- **Lean Operation:** 30-second polling interval prevents unnecessary load

## Deployment

### Production Stack
- **Frontend**: Vercel (via `lostbobo` repo at https://github.com/NexusBayArea/lostbobo.git)
- **Production URL**: https://simhpc.com
- **Backend**: RunPod GPU instance (A40)
- **Database**: Supabase PostgreSQL (No Git sync)
- **Cache/Queue**: Redis 7 (alpine)

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
